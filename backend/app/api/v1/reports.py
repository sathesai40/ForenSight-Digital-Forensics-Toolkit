from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.case import InvestigationCase
from app.models.evidence import EvidenceRecord
from app.models.security_event import SecurityEvent
from app.models.audit_record import AuditRecord
from app.forensics.reporter import generate_case_pdf_report

router = APIRouter(tags=["Forensic PDF Reports"])


def _find_case_by_identifier(case_id: str, db: Session) -> InvestigationCase:
    """Resolve investigation case by integer ID or unique case number string."""
    case = None
    if case_id.isdigit():
        case = db.query(InvestigationCase).filter(InvestigationCase.id == int(case_id)).first()
    if not case:
        case = db.query(InvestigationCase).filter(InvestigationCase.case_number == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case '{case_id}' was not found.",
        )
    return case


@router.get("/cases/{case_id}/report/pdf")
def export_case_pdf_report(
    case_id: str,
    operator: str = Query("Chief Forensic Examiner", description="Analyst requesting the export"),
    db: Session = Depends(get_db),
):
    """Generate and download a comprehensive, publication-quality forensic investigation PDF report.

    Contains full case metadata, evidence cryptographic hashes, verification integrity statuses,
    suspicious file indicators, security event telemetry, chronological timeline, and legal disclaimers.
    """
    case = _find_case_by_identifier(case_id, db)

    evidences = (
        db.query(EvidenceRecord)
        .filter(EvidenceRecord.case_id == case.id)
        .order_by(EvidenceRecord.id.asc())
        .all()
    )
    events = (
        db.query(SecurityEvent)
        .filter(SecurityEvent.case_id == case.id)
        .order_by(SecurityEvent.timestamp.asc())
        .all()
    )
    vault_dir = Path(settings.evidence_vault_dir)

    try:
        pdf_bytes = generate_case_pdf_report(
            case=case,
            evidences=evidences,
            events=events,
            vault_dir=vault_dir,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF report compilation failed: {str(e)}",
        )

    # Immutable Audit Log Record
    audit = AuditRecord(
        case_id=case.id,
        operator=operator,
        action="REPORT_GENERATED",
        target_type="CASE",
        target_id=case.case_number,
        details=f"Official forensic investigation PDF report generated ({len(pdf_bytes)} bytes). Included {len(evidences)} evidence artifacts and {len(events)} security events.",
    )
    db.add(audit)
    db.commit()

    filename = f"Forensic_Report_{case.case_number}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/cases/{case_id}/report/summary")
def get_case_report_summary(case_id: str, db: Session = Depends(get_db)):
    """Retrieve pre-export JSON summary of the case findings and report contents."""
    case = _find_case_by_identifier(case_id, db)

    evidences = (
        db.query(EvidenceRecord)
        .filter(EvidenceRecord.case_id == case.id)
        .order_by(EvidenceRecord.id.asc())
        .all()
    )
    events = (
        db.query(SecurityEvent)
        .filter(SecurityEvent.case_id == case.id)
        .order_by(SecurityEvent.timestamp.asc())
        .all()
    )

    sev_counts = {}
    for e in events:
        sev_counts[e.severity] = sev_counts.get(e.severity, 0) + 1

    verified_count = sum(1 for ev in evidences if ev.integrity_status == "VERIFIED")
    compromised_count = sum(1 for ev in evidences if ev.integrity_status == "COMPROMISED")

    return {
        "case_id": case.id,
        "case_number": case.case_number,
        "title": case.title,
        "status": case.status,
        "priority": case.priority,
        "investigator_name": case.investigator_name,
        "total_evidence": len(evidences),
        "verified_evidence": verified_count,
        "compromised_evidence": compromised_count,
        "total_events": len(events),
        "events_by_severity": sev_counts,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
