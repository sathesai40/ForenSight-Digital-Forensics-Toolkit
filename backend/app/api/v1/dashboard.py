import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.case import InvestigationCase
from app.models.evidence import EvidenceRecord
from app.models.security_event import SecurityEvent
from app.models.audit_record import AuditRecord
from app.schemas.dashboard import DashboardStatsResponse
from app.schemas.case import CaseResponse
from app.schemas.audit_record import AuditRecordResponse

router = APIRouter(prefix="/dashboard", tags=["Investigation Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_statistics(db: Session = Depends(get_db)) -> DashboardStatsResponse:
    """Retrieve comprehensive forensic workbench metrics computed strictly from persisted data.

    Returns real case tallies, evidence integrity breakdowns, event severity distributions,
    and recent non-repudiation audit actions. Never returns synthetic or placeholder values.
    """
    total_cases = db.query(InvestigationCase).count()

    # Cases grouped by status
    status_counts = (
        db.query(InvestigationCase.status, func.count(InvestigationCase.id))
        .group_by(InvestigationCase.status)
        .all()
    )
    cases_by_status: Dict[str, int] = {s: count for s, count in status_counts}

    # Cases grouped by priority
    priority_counts = (
        db.query(InvestigationCase.priority, func.count(InvestigationCase.id))
        .group_by(InvestigationCase.priority)
        .all()
    )
    cases_by_priority: Dict[str, int] = {p: count for p, count in priority_counts}

    # Evidence metrics
    total_evidence = db.query(EvidenceRecord).count()
    evidence_status_counts = (
        db.query(EvidenceRecord.integrity_status, func.count(EvidenceRecord.id))
        .group_by(EvidenceRecord.integrity_status)
        .all()
    )
    evidence_by_status: Dict[str, int] = {st: count for st, count in evidence_status_counts}

    sum_bytes = db.query(func.sum(EvidenceRecord.file_size_bytes)).scalar()
    total_evidence_bytes = int(sum_bytes) if sum_bytes else 0

    # Security Events metrics
    total_events = db.query(SecurityEvent).count()
    sev_counts = (
        db.query(SecurityEvent.severity, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.severity)
        .all()
    )
    events_by_severity: Dict[str, int] = {sev: count for sev, count in sev_counts}

    type_counts = (
        db.query(SecurityEvent.event_type, func.count(SecurityEvent.id))
        .group_by(SecurityEvent.event_type)
        .all()
    )
    events_by_type: Dict[str, int] = {t: count for t, count in type_counts}

    # Recent Audit Activity (last 6 records)
    recent_audits = (
        db.query(AuditRecord)
        .order_by(AuditRecord.timestamp.desc())
        .limit(6)
        .all()
    )
    recent_activity = [AuditRecordResponse.model_validate(a) for a in recent_audits]

    # Recent Cases (last 5 cases)
    recent_case_models = (
        db.query(InvestigationCase)
        .order_by(InvestigationCase.created_at.desc())
        .limit(5)
        .all()
    )
    recent_cases = []
    for c in recent_case_models:
        recent_cases.append(
            CaseResponse(
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
        )

    # Disk / Vault diagnostics
    vault_path = Path(settings.evidence_vault_dir).resolve()
    free_bytes = None
    try:
        _, _, free = shutil.disk_usage(vault_path.parent if not vault_path.exists() else vault_path)
        free_bytes = free
    except Exception:
        free_bytes = None

    system_status = {
        "database": "sqlite",
        "database_connected": True,
        "vault_ready": vault_path.exists() and vault_path.is_dir(),
        "free_storage_bytes": free_bytes,
        "server_time_utc": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
    }

    return DashboardStatsResponse(
        total_cases=total_cases,
        cases_by_status=cases_by_status,
        cases_by_priority=cases_by_priority,
        total_evidence=total_evidence,
        evidence_by_status=evidence_by_status,
        total_evidence_bytes=total_evidence_bytes,
        total_events=total_events,
        events_by_severity=events_by_severity,
        events_by_type=events_by_type,
        recent_activity=recent_activity,
        recent_cases=recent_cases,
        system_status=system_status,
    )
