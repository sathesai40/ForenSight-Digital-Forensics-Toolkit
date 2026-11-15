from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.case import InvestigationCase
from app.models.evidence import EvidenceRecord
from app.models.security_event import SecurityEvent
from app.models.audit_record import AuditRecord


def test_investigation_case_lifecycle(db_session: Session):
    """Verify InvestigationCase model persistence and fields."""
    case = InvestigationCase(
        case_number="FS-2026-TEST01",
        title="Unauthorized Database Dump Exfiltration",
        description="Suspicious high-volume outbound network transfer detected.",
        investigator_name="Specialist Hunter",
        lead_analyst="Analyst Vance",
        priority="HIGH",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    assert case.id is not None
    assert case.case_number == "FS-2026-TEST01"
    assert case.created_at is not None
    assert case.updated_at is not None
    assert case.status == "OPEN"
    assert case.priority == "HIGH"


def test_evidence_record_integrity(db_session: Session):
    """Verify EvidenceRecord model, SHA-256 hash persistence, and case association."""
    case = InvestigationCase(
        case_number="FS-2026-TEST02",
        title="Malware Extraction Case",
        investigator_name="Investigator Cruz",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    sha256_mock = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    evidence = EvidenceRecord(
        case_id=case.id,
        evidence_number="EVD-001",
        source_filename="suspicious_payload.bin",
        stored_filename="evd_uuid_suspicious_payload.bin",
        file_path="vault/2026/evd_uuid_suspicious_payload.bin",
        file_size_bytes=1048576,
        mime_type="application/octet-stream",
        sha256_hash=sha256_mock,
        md5_hash="d41d8cd98f00b204e9800998ecf8427e",
        acquired_by="Investigator Cruz",
        chain_of_custody_notes="Acquired via memory dump carving. Sealed into vault.",
        integrity_status="VERIFIED",
        is_read_only=True,
    )
    db_session.add(evidence)
    db_session.commit()
    db_session.refresh(evidence)

    assert evidence.id is not None
    assert evidence.case_id == case.id
    assert evidence.sha256_hash == sha256_mock
    assert evidence.is_read_only is True
    assert len(case.evidence_records) == 1
    assert case.evidence_records[0].source_filename == "suspicious_payload.bin"


def test_security_event_and_audit_record(db_session: Session):
    """Verify SecurityEvent and immutable AuditRecord schema and relations."""
    case = InvestigationCase(
        case_number="FS-2026-TEST03",
        title="Lateral Movement Analysis",
        investigator_name="Lead Analyst Sterling",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    event_time = datetime.now(timezone.utc)
    sec_event = SecurityEvent(
        case_id=case.id,
        timestamp=event_time,
        event_type="PRIVILEGE_ESCALATION",
        severity="CRITICAL",
        source_ip="10.0.4.15",
        destination_ip="10.0.1.5",
        user_account="svc_backup",
        description="Unauthorized privilege escalation detected via token impersonation.",
        indicator_tags="T1134,PrivilegeEscalation",
        raw_data='{"event_id": 4672, "privileges": ["SeDebugPrivilege"]}',
    )
    db_session.add(sec_event)

    audit = AuditRecord(
        case_id=case.id,
        operator="Lead Analyst Sterling",
        action="EVENT_FLAGGED",
        target_type="SECURITY_EVENT",
        target_id="4672",
        details="Critical privilege escalation event flagged for timeline inclusion.",
        ip_address="127.0.0.1",
    )
    db_session.add(audit)
    db_session.commit()

    assert sec_event.id is not None
    assert sec_event.severity == "CRITICAL"
    assert audit.id is not None
    assert audit.action == "EVENT_FLAGGED"
    assert len(case.security_events) == 1
    assert len(case.audit_records) == 1
