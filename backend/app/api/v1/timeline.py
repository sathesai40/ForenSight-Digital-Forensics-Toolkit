from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.case import InvestigationCase
from app.models.evidence import EvidenceRecord
from app.models.security_event import SecurityEvent
from app.models.audit_record import AuditRecord
from app.schemas.timeline import TimelineItemResponse, CaseTimelineResponse

router = APIRouter(tags=["Investigation Timeline"])


@router.get("/cases/{case_id}/timeline", response_model=CaseTimelineResponse)
def get_case_timeline(
    case_id: int,
    order: str = Query("asc", description="Sort order: 'asc' (chronological) or 'desc' (reverse)"),
    category: Optional[str] = Query(None, description="Filter by category: EVIDENCE_ACQUISITION, SECURITY_EVENT, INTEGRITY_CHECK, AUDIT_ACTION"),
    severity: Optional[str] = Query(None, description="Filter by severity: INFO, LOW, MEDIUM, HIGH, CRITICAL"),
    db: Session = Depends(get_db),
) -> CaseTimelineResponse:
    """Retrieve unified forensic timeline correlated across heterogeneous sources in strict UTC.

    Aggregates:
    1. Evidence acquisition milestones
    2. File analysis indicators & security log events
    3. Hash integrity verification results
    4. Chain-of-custody audit actions
    """
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID {case_id} was not found.",
        )

    timeline_items: List[TimelineItemResponse] = []

    # 1. Evidence Acquisition Milestones
    evidences = db.query(EvidenceRecord).filter(EvidenceRecord.case_id == case_id).all()
    for ev in evidences:
        timeline_items.append(
            TimelineItemResponse(
                id=f"evd-acq-{ev.id}",
                timestamp=ev.acquired_at,
                category="EVIDENCE_ACQUISITION",
                title=f"Evidence Acquired: {ev.evidence_number}",
                severity="INFO",
                description=f"Artifact '{ev.source_filename}' ({ev.file_size_bytes} bytes) secured into vault by {ev.acquired_by}. SHA-256: {ev.sha256_hash[:16]}...",
                source=ev.source_filename,
                metadata={
                    "evidence_id": ev.id,
                    "evidence_number": ev.evidence_number,
                    "sha256_hash": ev.sha256_hash,
                    "file_size_bytes": ev.file_size_bytes,
                    "mime_type": ev.mime_type,
                    "integrity_status": ev.integrity_status,
                },
            )
        )

    # 2. Security Events & Findings
    sec_events = db.query(SecurityEvent).filter(SecurityEvent.case_id == case_id).all()
    for se in sec_events:
        item_cat = "SECURITY_EVENT"
        if se.event_type == "SUSPICIOUS_INDICATOR":
            item_cat = "ANALYSIS_FINDING"

        timeline_items.append(
            TimelineItemResponse(
                id=f"sec-ev-{se.id}",
                timestamp=se.timestamp,
                category=item_cat,
                title=f"{se.event_type.replace('_', ' ').title()}",
                severity=se.severity,
                description=se.description,
                source=se.source_ip or se.user_account or "Log Stream",
                metadata={
                    "event_id": se.id,
                    "event_type": se.event_type,
                    "source_ip": se.source_ip,
                    "destination_ip": se.destination_ip,
                    "user_account": se.user_account,
                    "indicator_tags": se.indicator_tags,
                },
            )
        )

    # 3. Integrity Verifications & Key Audit Actions
    audits = db.query(AuditRecord).filter(AuditRecord.case_id == case_id).all()
    for au in audits:
        if au.action.startswith("INTEGRITY_"):
            sev = "INFO" if au.action == "INTEGRITY_VERIFIED" else "CRITICAL"
            timeline_items.append(
                TimelineItemResponse(
                    id=f"audit-int-{au.id}",
                    timestamp=au.timestamp,
                    category="INTEGRITY_CHECK",
                    title=f"Integrity Check: {au.target_id}",
                    severity=sev,
                    description=au.details,
                    source=au.operator,
                    metadata={
                        "audit_id": au.id,
                        "action": au.action,
                        "operator": au.operator,
                        "action_hash": au.action_hash,
                    },
                )
            )
        elif au.action in ["CASE_CREATED", "STATUS_CHANGED"]:
            timeline_items.append(
                TimelineItemResponse(
                    id=f"audit-act-{au.id}",
                    timestamp=au.timestamp,
                    category="AUDIT_ACTION",
                    title=f"Case Action: {au.action.replace('_', ' ').title()}",
                    severity="INFO",
                    description=au.details,
                    source=au.operator,
                    metadata={"audit_id": au.id, "action": au.action, "operator": au.operator},
                )
            )

    # Apply Category & Severity Filters if requested
    if category:
        timeline_items = [item for item in timeline_items if item.category.upper() == category.upper()]
    if severity:
        timeline_items = [item for item in timeline_items if item.severity.upper() == severity.upper()]

    # Sort strictly by timestamp in UTC
    reverse = (order.lower() == "desc")
    timeline_items.sort(key=lambda x: x.timestamp, reverse=reverse)

    return CaseTimelineResponse(
        case_id=case_id,
        case_number=case.case_number,
        total_events=len(timeline_items),
        timeline=timeline_items,
    )
