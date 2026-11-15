"""Phase 4 Automated Pytest Suite: Integration, Forensic Integrity, and Security Boundaries."""

import io
import os
import stat
import hashlib
from pathlib import Path
import pytest
from fastapi.testclient import TestClient


def test_phase4_e2e_unauthorized_access_workflow(client: TestClient):
    """Verifies complete investigation lifecycle from case creation to PDF generation."""
    # 1. Create Case
    res = client.post(
        "/api/v1/cases",
        json={
            "title": "Unauthorized Access Investigation",
            "description": "Synthetic brute-force and root elevation investigation.",
            "investigator_name": "Special Agent J. Vance",
            "priority": "HIGH",
        },
    )
    assert res.status_code == 201
    case = res.json()
    case_id = case["id"]
    case_number = case["case_number"]
    assert case["status"] == "OPEN"

    # 2. Update Status and Priority
    res = client.patch(
        f"/api/v1/cases/{case_id}?operator=Special%20Agent%20J.%20Vance",
        json={"status": "IN_PROGRESS", "priority": "CRITICAL"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "IN_PROGRESS"
    assert res.json()["priority"] == "CRITICAL"

    # 3. Upload Evidence
    evidence_bytes = b"FORENSIGHT_SYNTHETIC_EVIDENCE_DUMP_V1\nAcquisition Source: host-sec01:/var/log/audit.slice\n"
    expected_sha256 = hashlib.sha256(evidence_bytes).hexdigest()
    files = {"file": ("sample_evidence.bin", io.BytesIO(evidence_bytes), "application/octet-stream")}
    res = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        data={"investigator_name": "Special Agent J. Vance", "chain_of_custody_notes": "Live dump"},
        files=files,
    )
    assert res.status_code == 201
    evidence = res.json()
    evidence_id = evidence["id"]
    assert evidence["sha256_hash"] == expected_sha256
    assert evidence["integrity_status"] == "VERIFIED"

    # 4. Verify Hash
    res = client.post(f"/api/v1/evidence/{evidence_id}/verify?operator=Examiner")
    assert res.status_code == 200
    assert res.json()["status"] == "MATCH"

    # 5. Extract Metadata
    res = client.get(f"/api/v1/evidence/{evidence_id}/metadata")
    assert res.status_code == 200
    meta = res.json()
    assert meta["source_metadata"]["sha256_hash"] == expected_sha256
    assert "investigative_indicators" in meta

    # 6. Import Synthetic Authentication Logs
    auth_log = (
        "2026-11-15T02:00:10.000Z host-sec01 sshd[20101]: Failed password for invalid user admin from 198.51.100.99 port 41201 ssh2\n"
        "2026-11-15T02:00:15.000Z host-sec01 sshd[20102]: Failed password for invalid user root from 198.51.100.99 port 41202 ssh2\n"
        "2026-11-15T02:00:21.000Z host-sec01 sshd[20103]: Failed password for invalid user operator from 198.51.100.99 port 41203 ssh2\n"
        "2026-11-15T02:00:26.000Z host-sec01 sshd[20104]: Failed password for invalid user svc_backup from 198.51.100.99 port 41204 ssh2\n"
        "2026-11-15T02:00:32.000Z host-sec01 sshd[20105]: Failed password for invalid user forensic from 198.51.100.99 port 41205 ssh2\n"
        "2026-11-15T02:00:45.000Z host-sec01 sshd[20110]: Accepted password for svc_backup from 198.51.100.99 port 41210 ssh2\n"
        "2026-11-15T02:01:05.000Z host-sec01 sudo: svc_backup : TTY=pts/1 ; PWD=/home/svc_backup ; USER=root ; COMMAND=/bin/bash\n"
    )
    files = {"file": ("auth.log", io.BytesIO(auth_log.encode("utf-8")), "text/plain")}
    res = client.post(f"/api/v1/cases/{case_id}/logs/analyze", data={"operator": "Analyst"}, files=files)
    assert res.status_code == 201
    log_data = res.json()
    rule_ids = [f["rule"] for f in log_data["findings"]]
    assert "BRUTE_FORCE_IP_THRESHOLD" in rule_ids
    assert "BRUTE_FORCE_SUCCESS_SEQUENCE" in rule_ids

    # 7. Timeline Correlation
    res = client.get(f"/api/v1/cases/{case_id}/timeline")
    assert res.status_code == 200
    timeline = res.json()
    assert timeline["total_events"] > 0
    categories = {item["category"] for item in timeline["timeline"]}
    assert "EVIDENCE_ACQUISITION" in categories
    assert "SECURITY_EVENT" in categories

    # 8. Audit Trail Verification
    res = client.get(f"/api/v1/audit?case_id={case_id}")
    assert res.status_code == 200
    actions = [a["action"] for a in res.json()]
    assert "CASE_CREATED" in actions
    assert "STATUS_CHANGED" in actions
    assert "EVIDENCE_ACQUIRED" in actions
    assert "INTEGRITY_VERIFIED" in actions
    assert "LOGS_ANALYZED" in actions

    # 9. PDF Report Export
    res = client.get(f"/api/v1/cases/{case_id}/report/pdf?operator=Special%20Agent%20J.%20Vance")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF-1.4")
    assert len(res.content) > 5000


def test_phase4_security_boundary_validation(client: TestClient):
    """Verifies security controls, traversal defenses, and tampering detection."""
    # 1. Invalid Case 404
    res = client.get("/api/v1/cases/999999")
    assert res.status_code == 404

    # 2. Create target case
    res = client.post("/api/v1/cases", json={"title": "Security Scope Test", "investigator_name": "QA"})
    case_id = res.json()["id"]

    # 3. Oversized evidence (>25MB) rejected with 413
    oversized = b"0" * (26 * 1024 * 1024)
    res = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        data={"investigator_name": "QA"},
        files={"file": ("huge.raw", io.BytesIO(oversized), "application/octet-stream")},
    )
    assert res.status_code == 413

    # 4. Traversal filename sanitized
    traversal_files = {"file": ("../../../../etc/passwd", io.BytesIO(b"root:x:0:0:..."), "text/plain")}
    res = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        data={"investigator_name": "QA"},
        files=traversal_files,
    )
    assert res.status_code == 201
    traversal_evidence = res.json()
    assert not traversal_evidence["file_path"].startswith("..")
    assert "passwd" in traversal_evidence["stored_filename"]

    from app.config import settings
    vault_dir = Path(settings.evidence_vault_dir)

    # 5. Tampered Evidence Detection (MISMATCH)
    vault_file = vault_dir / traversal_evidence["stored_filename"]
    assert vault_file.exists(), f"Vault file should exist at {vault_file}"
    os.chmod(vault_file, stat.S_IWRITE | stat.S_IREAD)
    with open(vault_file, "wb") as f:
        f.write(b"CORRUPTED_BYTES")
    os.chmod(vault_file, stat.S_IREAD)

    res = client.post(f"/api/v1/evidence/{traversal_evidence['id']}/verify?operator=QA")
    assert res.status_code == 200
    assert res.json()["status"] == "MISMATCH"

    # 6. Missing Evidence on Disk Detection (ERROR)
    vanish_files = {"file": ("temporary.bin", io.BytesIO(b"vanish"), "application/octet-stream")}
    res = client.post(f"/api/v1/cases/{case_id}/evidence", data={"investigator_name": "QA"}, files=vanish_files)
    assert res.status_code == 201
    v_data = res.json()
    v_path = vault_dir / v_data["stored_filename"]
    assert v_path.exists(), f"Vanish file should exist at {v_path}"
    os.chmod(v_path, stat.S_IWRITE)
    os.remove(v_path)

    res = client.post(f"/api/v1/evidence/{v_data['id']}/verify?operator=QA")
    assert res.status_code == 200
    assert res.json()["status"] == "ERROR"

    # 7. Non-existent evidence 404
    res = client.post("/api/v1/evidence/999999/verify?operator=QA")
    assert res.status_code == 404

    # 8. Corrupted binary log safe handling
    res = client.post(
        f"/api/v1/cases/{case_id}/logs/analyze",
        data={"operator": "QA"},
        files={"file": ("corrupt.bin", io.BytesIO(b"\x00\xff\xfe\x01\x02"), "application/octet-stream")},
    )
    assert res.status_code in [200, 201, 400, 422]
