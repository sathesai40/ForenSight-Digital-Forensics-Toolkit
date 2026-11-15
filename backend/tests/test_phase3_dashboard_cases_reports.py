import io
import os
import hashlib
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.config import settings
from app.models.case import InvestigationCase
from app.models.evidence import EvidenceRecord
from app.models.security_event import SecurityEvent
from app.models.audit_record import AuditRecord


def test_dashboard_statistics_real_metrics(client: TestClient, db_session: Session, tmp_path: Path):
    """Test GET /api/v1/dashboard/stats computes real metrics from database without synthetic or fake values."""
    settings.evidence_vault_dir = str(tmp_path / "vault")

    # 1. Create cases with diverse statuses and priorities
    c1 = InvestigationCase(
        case_number=f"FS-2026-DASH1-{os.urandom(3).hex()}",
        title="Active APT Inquiry",
        investigator_name="Agent Vance",
        priority="CRITICAL",
        status="IN_PROGRESS",
    )
    c2 = InvestigationCase(
        case_number=f"FS-2026-DASH2-{os.urandom(3).hex()}",
        title="Archived Phishing Triage",
        investigator_name="Agent Miller",
        priority="LOW",
        status="CLOSED",
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    # 2. Add evidence to c1
    ev = EvidenceRecord(
        case_id=c1.id,
        evidence_number="EVD-001",
        source_filename="firewall_packet.pcap",
        stored_filename="evd_uuid_pcap.bin",
        file_path="vault/evd_uuid_pcap.bin",
        file_size_bytes=2048,
        mime_type="application/vnd.tcpdump.pcap",
        sha256_hash="a" * 64,
        acquired_by="Agent Vance",
        integrity_status="VERIFIED",
    )
    db_session.add(ev)

    # 3. Add security events
    se1 = SecurityEvent(
        case_id=c1.id,
        timestamp=c1.created_at,
        event_type="AUTHENTICATION",
        severity="HIGH",
        description="Repeated failed SSH logins",
    )
    se2 = SecurityEvent(
        case_id=c1.id,
        timestamp=c1.created_at,
        event_type="PRIVILEGE_ESCALATION",
        severity="CRITICAL",
        description="Root sudo execution",
    )
    db_session.add_all([se1, se2])
    db_session.commit()

    resp = client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    stats = resp.json()

    assert stats["total_cases"] >= 2
    assert "IN_PROGRESS" in stats["cases_by_status"]
    assert "CLOSED" in stats["cases_by_status"]
    assert "CRITICAL" in stats["cases_by_priority"]
    assert stats["total_evidence"] >= 1
    assert stats["evidence_by_status"].get("VERIFIED", 0) >= 1
    assert stats["total_evidence_bytes"] >= 2048
    assert stats["total_events"] >= 2
    assert stats["events_by_severity"].get("CRITICAL", 0) >= 1
    assert stats["events_by_severity"].get("HIGH", 0) >= 1
    assert len(stats["recent_cases"]) >= 2
    assert "database_connected" in stats["system_status"]


def test_case_status_transition_and_audit(client: TestClient, db_session: Session):
    """Test PATCH /api/v1/cases/{case_id} updates case status, priority, and records an immutable audit log."""
    case = InvestigationCase(
        case_number=f"FS-2026-PATCH-{os.urandom(3).hex()}",
        title="Unauthorized Data Exfiltration Investigation",
        description="Initial hypothesis: insider breach.",
        investigator_name="Analyst Sterling",
        priority="MEDIUM",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # Transition status: OPEN -> IN_PROGRESS, Priority: MEDIUM -> HIGH
    patch_resp = client.patch(
        f"/api/v1/cases/{case.id}?operator=Lead Examiner Ray",
        json={
            "status": "IN_PROGRESS",
            "priority": "HIGH",
            "description": "Updated hypothesis: confirmed external C2 beaconing.",
        },
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["status"] == "IN_PROGRESS"
    assert updated["priority"] == "HIGH"
    assert "external C2" in updated["description"]

    # Verify audit record was created for the status transition
    audit_resp = client.get(f"/api/v1/audit?case_id={case.id}")
    assert audit_resp.status_code == 200
    audits = audit_resp.json()
    status_audits = [a for a in audits if a["action"] == "STATUS_CHANGED"]
    assert len(status_audits) >= 1
    assert "status transitioned from OPEN to IN_PROGRESS" in status_audits[0]["details"]
    assert status_audits[0]["operator"] == "Lead Examiner Ray"


def test_pdf_report_generation_and_download(client: TestClient, db_session: Session, tmp_path: Path):
    """Test generating and downloading a genuine forensic investigation PDF report compiled from case data."""
    settings.evidence_vault_dir = str(tmp_path / "vault")
    (tmp_path / "vault").mkdir(parents=True, exist_ok=True)

    # Create Case
    case = InvestigationCase(
        case_number="FS-2026-REPORT-001",
        title="Operation Cyber Vault Breach Report",
        description="Forensic investigation into unauthorized root privilege escalation and memory dump extraction.",
        investigator_name="Chief Inspector Vance",
        lead_analyst="Senior Analyst Miller",
        priority="CRITICAL",
        status="UNDER_REVIEW",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    # Create Evidence on disk & DB
    evidence_content = b"%PDF-1.4 Fake Evidence Content for Verification"
    ev_sha = hashlib.sha256(evidence_content).hexdigest()
    ev_path = tmp_path / "vault" / "evd_sample.pdf"
    with open(ev_path, "wb") as f:
        f.write(evidence_content)

    evidence = EvidenceRecord(
        case_id=case.id,
        evidence_number="EVD-001",
        source_filename="sample_artifact.pdf",
        stored_filename="evd_sample.pdf",
        file_path="vault/evd_sample.pdf",
        file_size_bytes=len(evidence_content),
        mime_type="application/pdf",
        sha256_hash=ev_sha,
        acquired_by="Chief Inspector Vance",
        integrity_status="VERIFIED",
    )
    db_session.add(evidence)

    # Create Security Event
    sec_ev = SecurityEvent(
        case_id=case.id,
        timestamp=case.created_at,
        event_type="AUTHENTICATION",
        severity="HIGH",
        source_ip="198.51.100.42",
        user_account="root",
        description="Repeated failed password attempts for invalid user root",
    )
    db_session.add(sec_ev)
    db_session.commit()

    # 1. Test Report Summary JSON endpoint
    summary_resp = client.get(f"/api/v1/cases/{case.id}/report/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["case_number"] == "FS-2026-REPORT-001"
    assert summary["total_evidence"] == 1
    assert summary["total_events"] == 1
    assert summary["verified_evidence"] == 1

    # 2. Test PDF Download endpoint
    pdf_resp = client.get(f"/api/v1/cases/{case.id}/report/pdf?operator=Chief Inspector Vance")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert 'filename="Forensic_Report_FS-2026-REPORT-001.pdf"' in pdf_resp.headers["content-disposition"]
    assert "no-cache" in pdf_resp.headers.get("cache-control", "")

    # Test PDF download resolving via case_number string
    by_number_resp = client.get(f"/api/v1/cases/{case.case_number}/report/pdf?operator=Chief Inspector Vance")
    assert by_number_resp.status_code == 200
    assert by_number_resp.content.startswith(b"%PDF")

    # Verify that the returned bytes form a valid PDF file (starts with %PDF)
    pdf_bytes = pdf_resp.content
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")

    # Verify that an audit record for report generation was recorded
    audit = db_session.query(AuditRecord).filter(
        AuditRecord.case_id == case.id,
        AuditRecord.action == "REPORT_GENERATED",
    ).first()
    assert audit is not None
    assert audit.operator == "Chief Inspector Vance"
    assert "FS-2026-REPORT-001" in audit.target_id
