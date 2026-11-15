import mimetypes
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.case import InvestigationCase
from app.models.evidence import EvidenceRecord
from app.models.audit_record import AuditRecord
from app.schemas.evidence import (
    EvidenceResponse,
    EvidenceVerificationResponse,
    EvidenceMetadataResponse,
)
from app.forensics.vault import acquire_evidence_stream, sanitize_filename
from app.forensics.verifier import verify_evidence_integrity
from app.forensics.metadata import inspect_evidence_metadata

router = APIRouter(tags=["Evidence Vault & Integrity"])


def generate_evidence_number(db: Session, case_id: int) -> str:
    """Generate sequential evidence tag: EVD-001, EVD-002 for the case."""
    count = db.query(EvidenceRecord).filter(EvidenceRecord.case_id == case_id).count() + 1
    return f"EVD-{count:03d}"


@router.post("/cases/{case_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence_for_case(
    case_id: int,
    file: UploadFile = File(..., description="Evidence artifact binary file"),
    investigator_name: str = Form(..., description="Examiner handling acquisition"),
    chain_of_custody_notes: str = Form("", description="Acquisition notes and source device context"),
    db: Session = Depends(get_db),
) -> EvidenceResponse:
    """Upload and acquire a new forensic evidence artifact for an investigation case.

    Preserves original bytes in an isolated storage vault, calculates cryptographic
    SHA-256 and MD5 hashes during acquisition stream, enforces file size caps,
    and appends an immutable audit record.
    """
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID {case_id} was not found.",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    vault_dir = Path(settings.evidence_vault_dir)
    max_bytes = settings.max_evidence_size_mb * 1024 * 1024

    try:
        acquired = acquire_evidence_stream(
            stream=file.file,
            original_filename=file.filename,
            vault_dir=vault_dir,
            max_size_bytes=max_bytes,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forensic vault acquisition failed: {str(e)}",
        )

    # Determine best MIME type
    detected_mime = file.content_type
    if not detected_mime or detected_mime == "application/octet-stream":
        guessed, _ = mimetypes.guess_type(acquired["source_filename"])
        detected_mime = guessed or "application/octet-stream"

    evidence_num = generate_evidence_number(db, case_id)

    evidence = EvidenceRecord(
        case_id=case_id,
        evidence_number=evidence_num,
        source_filename=acquired["source_filename"],
        stored_filename=acquired["stored_filename"],
        file_path=acquired["file_path"],
        file_size_bytes=acquired["file_size_bytes"],
        mime_type=detected_mime,
        sha256_hash=acquired["sha256_hash"],
        md5_hash=acquired["md5_hash"],
        acquired_by=investigator_name,
        acquired_at=acquired["acquired_at"],
        chain_of_custody_notes=chain_of_custody_notes,
        integrity_status="VERIFIED",
        is_read_only=True,
    )
    db.add(evidence)
    db.flush()

    # Immutable Audit Log Entry
    audit = AuditRecord(
        case_id=case_id,
        operator=investigator_name,
        action="EVIDENCE_ACQUIRED",
        target_type="EVIDENCE",
        target_id=evidence.evidence_number,
        details=f"Acquired artifact '{evidence.source_filename}' ({evidence.file_size_bytes} bytes). SHA-256: {evidence.sha256_hash}",
        action_hash=evidence.sha256_hash,
    )
    db.add(audit)
    db.commit()
    db.refresh(evidence)

    return EvidenceResponse.model_validate(evidence)


@router.get("/cases/{case_id}/evidence", response_model=List[EvidenceResponse])
def list_case_evidence(case_id: int, db: Session = Depends(get_db)) -> List[EvidenceResponse]:
    """Retrieve all evidence records linked to a specific investigation case."""
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID {case_id} was not found.",
        )
    records = db.query(EvidenceRecord).filter(EvidenceRecord.case_id == case_id).order_by(EvidenceRecord.id.asc()).all()
    return [EvidenceResponse.model_validate(r) for r in records]


@router.get("/evidence", response_model=List[EvidenceResponse])
def list_all_evidence(
    case_id: Optional[int] = Query(None, description="Filter by case ID"),
    db: Session = Depends(get_db),
) -> List[EvidenceResponse]:
    """List evidence records across all cases or filtered by case ID."""
    query = db.query(EvidenceRecord)
    if case_id is not None:
        query = query.filter(EvidenceRecord.case_id == case_id)
    records = query.order_by(EvidenceRecord.id.desc()).all()
    return [EvidenceResponse.model_validate(r) for r in records]


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
def get_evidence_record(evidence_id: int, db: Session = Depends(get_db)) -> EvidenceResponse:
    """Retrieve specific evidence record by ID."""
    evidence = db.query(EvidenceRecord).filter(EvidenceRecord.id == evidence_id).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence artifact with ID {evidence_id} was not found.",
        )
    return EvidenceResponse.model_validate(evidence)


@router.post("/evidence/{evidence_id}/verify", response_model=EvidenceVerificationResponse)
def verify_evidence_hash(
    evidence_id: int,
    operator: str = Query("Forensic Examiner", description="Operator requesting cryptographic verification"),
    db: Session = Depends(get_db),
) -> EvidenceVerificationResponse:
    """Recalculate cryptographic SHA-256 hash from disk bytes and compare with original hash.

    Never overwrites original acquisition hash. Updates integrity_status and logs audit trail.
    """
    evidence = db.query(EvidenceRecord).filter(EvidenceRecord.id == evidence_id).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence artifact with ID {evidence_id} was not found.",
        )

    vault_dir = Path(settings.evidence_vault_dir)
    res = verify_evidence_integrity(
        vault_dir=vault_dir,
        stored_filename=evidence.stored_filename,
        original_sha256=evidence.sha256_hash,
    )

    # Update record status in DB based on verification outcome
    if res["status"] == "MATCH":
        evidence.integrity_status = "VERIFIED"
        action_name = "INTEGRITY_VERIFIED"
    elif res["status"] == "MISMATCH":
        evidence.integrity_status = "COMPROMISED"
        action_name = "INTEGRITY_MISMATCH"
    else:
        evidence.integrity_status = "ERROR"
        action_name = "INTEGRITY_ERROR"

    audit = AuditRecord(
        case_id=evidence.case_id,
        operator=operator,
        action=action_name,
        target_type="EVIDENCE",
        target_id=evidence.evidence_number,
        details=f"Verification status: {res['status']}. Expected: {res['expected_sha256']}, Calculated: {res['calculated_sha256']}. {res['detail']}",
        action_hash=res["calculated_sha256"] or res["expected_sha256"],
    )
    db.add(audit)
    db.commit()
    db.refresh(evidence)

    return EvidenceVerificationResponse(
        evidence_id=evidence.id,
        evidence_number=evidence.evidence_number,
        status=res["status"],
        expected_sha256=res["expected_sha256"],
        calculated_sha256=res["calculated_sha256"],
        verified_at=res["verified_at"],
        detail=res["detail"],
        file_exists=res["file_exists"],
    )


@router.get("/evidence/{evidence_id}/metadata", response_model=EvidenceMetadataResponse)
def get_evidence_metadata(evidence_id: int, db: Session = Depends(get_db)) -> EvidenceMetadataResponse:
    """Extract deep file metadata, signature magic bytes, and heuristic suspicious indicators."""
    evidence = db.query(EvidenceRecord).filter(EvidenceRecord.id == evidence_id).first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence artifact with ID {evidence_id} was not found.",
        )

    vault_dir = Path(settings.evidence_vault_dir)
    meta = inspect_evidence_metadata(
        vault_dir=vault_dir,
        stored_filename=evidence.stored_filename,
        source_filename=evidence.source_filename,
        acquired_at=evidence.acquired_at,
        original_sha256=evidence.sha256_hash,
        md5_hash=evidence.md5_hash,
    )

    return EvidenceMetadataResponse(
        evidence_id=evidence.id,
        evidence_number=evidence.evidence_number,
        source_metadata=meta["source_metadata"],
        vault_storage_metadata=meta["vault_storage_metadata"],
        signature_analysis=meta["signature_analysis"],
        investigative_indicators=meta["investigative_indicators"],
    )
