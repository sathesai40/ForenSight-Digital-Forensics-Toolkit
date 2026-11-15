from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.case import InvestigationCase
from app.models.audit_record import AuditRecord
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate

router = APIRouter(prefix="/cases", tags=["Investigation Cases"])


def generate_case_number(db: Session) -> str:
    """Generate sequential case number: FS-YYYY-XXXX."""
    year = datetime.now(timezone.utc).year
    count = db.query(InvestigationCase).count() + 1
    return f"FS-{year}-{count:04d}"


@router.get("", response_model=List[CaseResponse])
def list_cases(
    status_filter: Optional[str] = Query(None, description="Filter by status: OPEN, IN_PROGRESS, UNDER_REVIEW, CLOSED, ARCHIVED"),
    priority_filter: Optional[str] = Query(None, description="Filter by priority: LOW, MEDIUM, HIGH, CRITICAL"),
    db: Session = Depends(get_db),
) -> List[CaseResponse]:
    """Retrieve all investigation cases with optional filtering."""
    query = db.query(InvestigationCase)
    if status_filter:
        query = query.filter(InvestigationCase.status == status_filter.upper())
    if priority_filter:
        query = query.filter(InvestigationCase.priority == priority_filter.upper())

    cases = query.order_by(InvestigationCase.created_at.desc()).all()
    results = []
    for c in cases:
        resp = CaseResponse(
            id=c.id,
            case_number=c.case_number,
            title=c.title,
            description=c.description,
            investigator_name=c.investigator_name,
            lead_analyst=c.lead_analyst,
            status=c.status,
            priority=c.priority,
            created_at=c.created_at,
            updated_at=c.updated_at,
            evidence_count=len(c.evidence_records),
            events_count=len(c.security_events),
        )
        results.append(resp)
    return results


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)) -> CaseResponse:
    """Create a new investigation case with audit log record."""
    case_num = payload.case_number or generate_case_number(db)

    # Check for duplicate case_number
    existing = db.query(InvestigationCase).filter(InvestigationCase.case_number == case_num).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case number '{case_num}' already exists.",
        )

    case = InvestigationCase(
        case_number=case_num,
        title=payload.title,
        description=payload.description,
        investigator_name=payload.investigator_name,
        lead_analyst=payload.lead_analyst,
        priority=payload.priority,
        status="OPEN",
    )
    db.add(case)
    db.flush()

    # Immutable Audit entry
    audit = AuditRecord(
        case_id=case.id,
        operator=payload.investigator_name,
        action="CASE_CREATED",
        target_type="CASE",
        target_id=case.case_number,
        details=f"Case '{case.title}' created with priority {case.priority}",
    )
    db.add(audit)
    db.commit()
    db.refresh(case)

    return CaseResponse(
        id=case.id,
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        investigator_name=case.investigator_name,
        lead_analyst=case.lead_analyst,
        status=case.status,
        priority=case.priority,
        created_at=case.created_at,
        updated_at=case.updated_at,
        evidence_count=0,
        events_count=0,
    )


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)) -> CaseResponse:
    """Retrieve details for a specific investigation case."""
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return CaseResponse(
        id=case.id,
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        investigator_name=case.investigator_name,
        lead_analyst=case.lead_analyst,
        status=case.status,
        priority=case.priority,
        created_at=case.created_at,
        updated_at=case.updated_at,
        evidence_count=len(case.evidence_records),
        events_count=len(case.security_events),
    )


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: int,
    payload: CaseUpdate,
    operator: str = Query("Forensic Specialist", description="Operator performing modification"),
    db: Session = Depends(get_db),
) -> CaseResponse:
    """Update case status, priority, description, or assigned analysts with full audit logging."""
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    changes = []
    old_status = case.status

    if payload.title is not None and payload.title != case.title:
        changes.append(f"title changed to '{payload.title}'")
        case.title = payload.title
    if payload.description is not None and payload.description != case.description:
        changes.append("description updated")
        case.description = payload.description
    if payload.investigator_name is not None and payload.investigator_name != case.investigator_name:
        changes.append(f"investigator changed to '{payload.investigator_name}'")
        case.investigator_name = payload.investigator_name
    if payload.lead_analyst is not None and payload.lead_analyst != case.lead_analyst:
        changes.append(f"lead analyst changed to '{payload.lead_analyst}'")
        case.lead_analyst = payload.lead_analyst
    if payload.priority is not None and payload.priority != case.priority:
        changes.append(f"priority transitioned from {case.priority} to {payload.priority}")
        case.priority = payload.priority
    if payload.status is not None and payload.status != case.status:
        changes.append(f"status transitioned from {case.status} to {payload.status}")
        case.status = payload.status

    if changes:
        action = "STATUS_CHANGED" if (payload.status is not None and payload.status != old_status) else "CASE_UPDATED"
        audit = AuditRecord(
            case_id=case.id,
            operator=operator,
            action=action,
            target_type="CASE",
            target_id=case.case_number,
            details=f"Case {case.case_number} modified: " + "; ".join(changes),
        )
        db.add(audit)
        db.commit()
        db.refresh(case)

    return CaseResponse(
        id=case.id,
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        investigator_name=case.investigator_name,
        lead_analyst=case.lead_analyst,
        status=case.status,
        priority=case.priority,
        created_at=case.created_at,
        updated_at=case.updated_at,
        evidence_count=len(case.evidence_records),
        events_count=len(case.security_events),
    )
