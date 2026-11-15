import io
import os
import hashlib
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.config import settings


def test_complete_phase2_forensics_workflow(client: TestClient, db_session: Session, tmp_path: Path):
    """End-to-end verification of Phase 2:

    1. Case creation
    2. Evidence artifact upload & SHA-256 calculation
    3. Metadata inspection (signature & indicators)
    4. Cryptographic integrity hash verification (MATCH)
    5. Security log ingestion & brute force detection
    6. Unified chronological timeline retrieval
    7. Audit trail validation
    """
    settings.evidence_vault_dir = str(tmp_path / "vault")

    # Step 1: Create Case
    case_resp = client.post(
        "/api/v1/cases",
        json={
            "title": "Operation Sovereign Shield - Data Breach",
            "description": "Exfiltration attempt on core financial databases.",
            "investigator_name": "Chief Examiner Vance",
            "priority": "CRITICAL",
        },
    )
    assert case_resp.status_code == 201
    case_id = case_resp.json()["id"]

    # Step 2: Upload Evidence
    raw_evidence_bytes = b"EVIDENCE FORENSIC DUMP 2026-11-15 001"
    expected_hash = hashlib.sha256(raw_evidence_bytes).hexdigest()

    upload_resp = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        files={"file": ("memory_snapshot.raw", io.BytesIO(raw_evidence_bytes), "application/octet-stream")},
        data={
            "investigator_name": "Chief Examiner Vance",
            "chain_of_custody_notes": "Live RAM capture via hardware write blocker.",
        },
    )
    assert upload_resp.status_code == 201
    evidence = upload_resp.json()
    evidence_id = evidence["id"]
    assert evidence["sha256_hash"] == expected_hash
    assert evidence["evidence_number"] == "EVD-001"
    assert evidence["integrity_status"] == "VERIFIED"

    # Step 3: Inspect Metadata
    meta_resp = client.get(f"/api/v1/evidence/{evidence_id}/metadata")
    assert meta_resp.status_code == 200
    meta = meta_resp.json()
    assert meta["source_metadata"]["source_filename"] == "memory_snapshot.raw"
    assert meta["source_metadata"]["sha256_hash"] == expected_hash

    # Step 4: Verify Integrity Hash
    verify_resp = client.post(f"/api/v1/evidence/{evidence_id}/verify?operator=Chief Examiner Vance")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "MATCH"
    assert verify_resp.json()["calculated_sha256"] == expected_hash

    # Step 5: Ingest Security Logs with Brute Force
    auth_log_content = """
2026-11-15T04:10:01.000Z host-db01 sshd[901]: Failed password for root from 198.51.100.99 port 50001 ssh2
2026-11-15T04:10:04.000Z host-db01 sshd[902]: Failed password for root from 198.51.100.99 port 50002 ssh2
2026-11-15T04:10:08.000Z host-db01 sshd[903]: Failed password for root from 198.51.100.99 port 50003 ssh2
2026-11-15T04:11:00.000Z host-db01 sudo: forensic_user : TTY=pts/0 ; PWD=/root ; USER=root ; COMMAND=/bin/bash
""".strip()

    log_resp = client.post(
        f"/api/v1/cases/{case_id}/logs/analyze",
        data={"content": auth_log_content, "evidence_id": evidence_id, "operator": "Chief Examiner Vance"},
    )
    assert log_resp.status_code == 201
    log_data = log_resp.json()
    assert log_data["total_parsed"] == 4
    assert any(f["rule"] == "BRUTE_FORCE_IP_THRESHOLD" for f in log_data["findings"])

    # Step 6: Query Unified Chronological Timeline
    timeline_resp = client.get(f"/api/v1/cases/{case_id}/timeline?order=asc")
    assert timeline_resp.status_code == 200
    timeline_data = timeline_resp.json()
    assert timeline_data["total_events"] >= 6

    # Verify categories present
    categories = {item["category"] for item in timeline_data["timeline"]}
    assert "EVIDENCE_ACQUISITION" in categories
    assert "SECURITY_EVENT" in categories
    assert "INTEGRITY_CHECK" in categories

    # Step 7: Verify Audit Trail Recorded Actions
    audit_resp = client.get(f"/api/v1/audit?case_id={case_id}")
    assert audit_resp.status_code == 200
    audits = audit_resp.json()
    actions = [a["action"] for a in audits]
    assert "CASE_CREATED" in actions
    assert "EVIDENCE_ACQUIRED" in actions
    assert "INTEGRITY_VERIFIED" in actions
    assert "LOGS_ANALYZED" in actions
