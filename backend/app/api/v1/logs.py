from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.case import InvestigationCase
from app.models.evidence import EvidenceRecord
from app.models.security_event import SecurityEvent
from app.models.audit_record import AuditRecord
from app.schemas.security_event import SecurityEventResponse, LogAnalysisSummaryResponse
from app.forensics.log_parser import parse_and_analyze_log_stream

def _normalize_dt(dt: Optional[datetime]) -> Optional[datetime]:
    """Strip timezone for deterministic UTC comparison with naive SQLite datetime fields."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0)
    return dt.replace(microsecond=0)


router = APIRouter(tags=["Security Log Analysis"])


@router.post("/cases/{case_id}/logs/analyze", response_model=LogAnalysisSummaryResponse, status_code=status.HTTP_201_CREATED)
async def analyze_and_import_logs(
    case_id: int,
    file: Optional[UploadFile] = File(None, description="CSV or syslog file to ingest"),
    content: Optional[str] = Form(None, description="Direct raw log text content"),
    evidence_id: Optional[int] = Form(None, description="Optional linked evidence record ID"),
    operator: str = Form("Forensic Analyst", description="Investigator performing the analysis"),
    db: Session = Depends(get_db),
) -> LogAnalysisSummaryResponse:
    """Import and analyze security logs (CSV or auth.log/syslog format).

    Executes deterministic forensic detection rules:
    - Normalizes event timestamps to UTC
    - Flags failed and successful logins
    - Detects brute-force bursts (>=3 attempts from same IP/user)
    - Detects compromised account sequences (brute-force followed by login)
    - Records findings into SecurityEvent model and immutable audit trail.
    """
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID {case_id} was not found.",
        )

    if evidence_id is not None:
        evidence = db.query(EvidenceRecord).filter(
            EvidenceRecord.id == evidence_id,
            EvidenceRecord.case_id == case_id,
        ).first()
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evidence record {evidence_id} was not found for case {case_id}.",
            )

    raw_text = ""
    source_filename = ""
    if file is not None and file.filename:
        source_filename = file.filename
        try:
            byte_content = await file.read()
            raw_text = byte_content.decode("utf-8", errors="replace")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read uploaded log file: {str(e)}",
            )
    elif content:
        raw_text = content
        source_filename = "direct_input.log"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either a log file or raw text content for analysis.",
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Log content cannot be empty.",
        )

    parsed_events, findings = parse_and_analyze_log_stream(raw_text, filename=source_filename)

    if not parsed_events:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unable to parse valid security events from the provided log stream.",
        )

    # Query existing events for this case to avoid unintended duplicate entries and findings on repeated imports
    existing_events = db.query(SecurityEvent).filter(SecurityEvent.case_id == case_id).all()

    existing_event_keys = {
        (
            _normalize_dt(e.timestamp),
            e.event_type,
            (e.raw_data or "").strip(),
            (e.description or "").strip(),
        )
        for e in existing_events
        if e.event_type != "SUSPICIOUS_INDICATOR"
    }

    existing_findings_keys = {
        (
            (e.description or "").strip(),
            e.source_ip,
            e.user_account,
        )
        for e in existing_events
        if e.event_type == "SUSPICIOUS_INDICATOR"
    }

    created_events: List[SecurityEvent] = []
    newly_added_count = 0

    for pe in parsed_events:
        ts_key = _normalize_dt(pe.get("timestamp"))
        pe_key = (
            ts_key,
            pe["event_type"],
            (pe.get("raw_data") or "").strip(),
            (pe.get("description") or "").strip(),
        )

        if pe_key in existing_event_keys:
            existing_rec = next(
                (
                    e for e in existing_events
                    if (
                        _normalize_dt(e.timestamp),
                        e.event_type,
                        (e.raw_data or "").strip(),
                        (e.description or "").strip(),
                    ) == pe_key
                ),
                None,
            )
            if existing_rec:
                created_events.append(existing_rec)
            continue

        sec_ev = SecurityEvent(
            case_id=case_id,
            evidence_id=evidence_id,
            timestamp=pe["timestamp"],
            event_type=pe["event_type"],
            severity=pe["severity"],
            source_ip=pe.get("source_ip"),
            destination_ip=pe.get("destination_ip"),
            user_account=pe.get("user_account"),
            description=pe["description"],
            raw_data=pe.get("raw_data", ""),
            indicator_tags=pe.get("indicator_tags", ""),
        )
        db.add(sec_ev)
        created_events.append(sec_ev)
        existing_event_keys.add(pe_key)
        newly_added_count += 1

    # Persist suspicious indicator findings while preventing duplicate finding alerts on re-import
    ref_timestamp = parsed_events[-1]["timestamp"] if parsed_events else datetime.now(timezone.utc)
    for f in findings:
        f_desc = (f.get("description") or "").strip()
        f_key = (f_desc, f.get("source_ip"), f.get("user_account"))

        if f_key in existing_findings_keys:
            existing_f = next(
                (
                    e for e in existing_events
                    if e.event_type == "SUSPICIOUS_INDICATOR"
                    and (e.description or "").strip() == f_desc
                    and e.source_ip == f.get("source_ip")
                    and e.user_account == f.get("user_account")
                ),
                None,
            )
            if existing_f:
                created_events.append(existing_f)
            continue

        finding_ev = SecurityEvent(
            case_id=case_id,
            evidence_id=evidence_id,
            timestamp=ref_timestamp,
            event_type="SUSPICIOUS_INDICATOR",
            severity=f["severity"],
            source_ip=f.get("source_ip"),
            user_account=f.get("user_account"),
            description=f["description"],
            raw_data=str(f),
            indicator_tags=f.get("indicator_tags", "SuspiciousIndicator"),
        )
        db.add(finding_ev)
        created_events.append(finding_ev)
        existing_findings_keys.add(f_key)
        newly_added_count += 1

    # Immutable Audit Log Record
    audit = AuditRecord(
        case_id=case_id,
        operator=operator,
        action="LOGS_ANALYZED",
        target_type="SECURITY_EVENT",
        target_id=f"case-{case_id}",
        details=f"Parsed {len(parsed_events)} events from '{source_filename}'. Detected {len(findings)} suspicious indicators ({newly_added_count} new records stored, {len(created_events) - newly_added_count} existing retained).",
    )
    db.add(audit)
    db.commit()

    for ev in created_events:
        db.refresh(ev)

    return LogAnalysisSummaryResponse(
        case_id=case_id,
        total_parsed=len(parsed_events),
        events_stored=len(created_events),
        indicators_detected=len(findings),
        findings=findings,
        events=[SecurityEventResponse.model_validate(ev) for ev in created_events],
    )


@router.get("/cases/{case_id}/events", response_model=List[SecurityEventResponse])
def list_case_events(
    case_id: int,
    severity: Optional[str] = Query(None, description="Filter by severity: INFO, LOW, MEDIUM, HIGH, CRITICAL"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[SecurityEventResponse]:
    """Retrieve normalized security events for a specific investigation case."""
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID {case_id} was not found.",
        )

    query = db.query(SecurityEvent).filter(SecurityEvent.case_id == case_id)
    if severity:
        query = query.filter(SecurityEvent.severity == severity.upper())
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type.upper())

    records = query.order_by(SecurityEvent.timestamp.desc()).limit(limit).all()
    return [SecurityEventResponse.model_validate(r) for r in records]
