import hashlib
import io
import os
import shutil
import stat
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.config import settings
from app.models.case import InvestigationCase
from app.models.audit_record import AuditRecord


def create_test_case(db_session: Session) -> InvestigationCase:
    case = InvestigationCase(
        case_number=f"FS-2026-EVDTEST-{os.urandom(4).hex()}",
        title="Evidence Vault Test Case",
        description="Testing evidence acquisition and integrity checks.",
        investigator_name="Detective Miller",
        priority="HIGH",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


def test_evidence_upload_valid(client: TestClient, db_session: Session, tmp_path: Path):
    """Test valid evidence acquisition, SHA-256 calculation, and audit trail generation."""
    settings.evidence_vault_dir = str(tmp_path / "vault")
    case = create_test_case(db_session)

    content = b"CRITICAL FORENSIC EVIDENCE ARTIFACT MEMORY DUMP HEADER"
    expected_sha256 = hashlib.sha256(content).hexdigest()
    expected_md5 = hashlib.md5(content).hexdigest()

    response = client.post(
        f"/api/v1/cases/{case.id}/evidence",
        files={"file": ("memory_dump.raw", io.BytesIO(content), "application/octet-stream")},
        data={
            "investigator_name": "Detective Miller",
            "chain_of_custody_notes": "Acquired from workstation WS-01 RAM.",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["case_id"] == case.id
    assert data["evidence_number"] == "EVD-001"
    assert data["source_filename"] == "memory_dump.raw"
    assert data["sha256_hash"] == expected_sha256
    assert data["md5_hash"] == expected_md5
    assert data["file_size_bytes"] == len(content)
    assert data["integrity_status"] == "VERIFIED"
    assert data["is_read_only"] is True
    # Ensure no absolute filesystem path is exposed
    assert not data["file_path"].startswith("C:")
    assert not data["file_path"].startswith("D:")
    assert data["file_path"].startswith("vault/")

    # Verify audit record was created
    audit = db_session.query(AuditRecord).filter(
        AuditRecord.case_id == case.id,
        AuditRecord.action == "EVIDENCE_ACQUIRED",
    ).first()
    assert audit is not None
    assert audit.target_id == "EVD-001"
    assert audit.operator == "Detective Miller"
    assert expected_sha256 in audit.details


def test_evidence_upload_missing_case(client: TestClient):
    """Test uploading to a non-existent case returns 404."""
    content = b"some data"
    response = client.post(
        "/api/v1/cases/999999/evidence",
        files={"file": ("evidence.bin", io.BytesIO(content), "application/octet-stream")},
        data={"investigator_name": "Specialist Vance"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_evidence_upload_oversized_rejection(client: TestClient, db_session: Session, tmp_path: Path):
    """Test oversized file rejection and verify cleanup."""
    settings.evidence_vault_dir = str(tmp_path / "vault")
    original_limit = settings.max_evidence_size_mb
    try:
        # Temporarily set max limit to 0 MB (100 bytes max)
        settings.max_evidence_size_mb = 0  # 0 MB implies 0 bytes limit in formula or test with 1MB
        case = create_test_case(db_session)

        # Force a small max_size test by setting max_evidence_size_mb to 1 and passing 2MB
        settings.max_evidence_size_mb = 1
        oversized_content = b"A" * (1024 * 1024 + 1024)  # > 1 MB

        response = client.post(
            f"/api/v1/cases/{case.id}/evidence",
            files={"file": ("large_payload.bin", io.BytesIO(oversized_content), "application/octet-stream")},
            data={"investigator_name": "Detective Miller"},
        )
        assert response.status_code == 413
        assert "exceeds maximum limit" in response.json()["detail"]

        # Ensure no files left in vault
        vault_files = list((tmp_path / "vault").glob("*large_payload*"))
        assert len(vault_files) == 0

    finally:
        settings.max_evidence_size_mb = original_limit


def test_evidence_upload_unsafe_filename_sanitization(client: TestClient, db_session: Session, tmp_path: Path):
    """Test path traversal and unsafe characters are neutralized."""
    settings.evidence_vault_dir = str(tmp_path / "vault")
    case = create_test_case(db_session)

    content = b"malicious traversal attempt"
    unsafe_name = "../../../../../windows/system32/cmd.exe"

    response = client.post(
        f"/api/v1/cases/{case.id}/evidence",
        files={"file": (unsafe_name, io.BytesIO(content), "application/octet-stream")},
        data={"investigator_name": "Forensic Specialist"},
    )
    assert response.status_code == 201
    data = response.json()
    assert ".." not in data["source_filename"]
    assert "/" not in data["source_filename"]
    assert "\\" not in data["source_filename"]
    assert data["source_filename"] == "cmd.exe"


def test_evidence_hash_verification_match_and_mismatch(client: TestClient, db_session: Session, tmp_path: Path):
    """Test cryptographic SHA-256 verification: MATCH, MISMATCH (after tampering), and ERROR (file removed)."""
    settings.evidence_vault_dir = str(tmp_path / "vault")
    case = create_test_case(db_session)

    content = b"ORIGINAL UNTAMPERED EVIDENCE BYTES 123456"
    upload_resp = client.post(
        f"/api/v1/cases/{case.id}/evidence",
        files={"file": ("secure_artifact.bin", io.BytesIO(content), "application/octet-stream")},
        data={"investigator_name": "Lead Examiner"},
    )
    assert upload_resp.status_code == 201
    evidence_id = upload_resp.json()["id"]
    stored_name = upload_resp.json()["stored_filename"]
    expected_sha = upload_resp.json()["sha256_hash"]

    # 1. Verification MATCH
    verify_resp = client.post(f"/api/v1/evidence/{evidence_id}/verify?operator=Lead Examiner")
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    assert v_data["status"] == "MATCH"
    assert v_data["expected_sha256"] == expected_sha
    assert v_data["calculated_sha256"] == expected_sha
    assert v_data["file_exists"] is True

    # 2. Tampering file -> Verification MISMATCH
    stored_file_path = tmp_path / "vault" / stored_name
    # Remove read-only attribute to simulate tampering
    stored_file_path.chmod(stat.S_IWRITE)
    with open(stored_file_path, "wb") as f:
        f.write(b"TAMPERED EVIDENCE CORRUPTED BYTES")

    verify_tampered = client.post(f"/api/v1/evidence/{evidence_id}/verify?operator=Lead Examiner")
    assert verify_tampered.status_code == 200
    vt_data = verify_tampered.json()
    assert vt_data["status"] == "MISMATCH"
    assert vt_data["expected_sha256"] == expected_sha
    assert vt_data["calculated_sha256"] != expected_sha

    # 3. Missing file -> Verification ERROR
    stored_file_path.unlink()
    verify_missing = client.post(f"/api/v1/evidence/{evidence_id}/verify?operator=Lead Examiner")
    assert verify_missing.status_code == 200
    vm_data = verify_missing.json()
    assert vm_data["status"] == "ERROR"
    assert vm_data["file_exists"] is False


def test_evidence_metadata_and_indicators(client: TestClient, db_session: Session, tmp_path: Path):
    """Test file metadata inspection, double extension detection, and magic bytes."""
    settings.evidence_vault_dir = str(tmp_path / "vault")
    case = create_test_case(db_session)

    # Fake double extension file with Windows PE executable magic header (MZ)
    pe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00" + b"\x00" * 100
    upload_resp = client.post(
        f"/api/v1/cases/{case.id}/evidence",
        files={"file": ("invoice_scan.pdf.exe", io.BytesIO(pe_content), "application/octet-stream")},
        data={"investigator_name": "Detective Miller"},
    )
    assert upload_resp.status_code == 201
    evidence_id = upload_resp.json()["id"]

    meta_resp = client.get(f"/api/v1/evidence/{evidence_id}/metadata")
    assert meta_resp.status_code == 200
    meta = meta_resp.json()

    assert meta["source_metadata"]["source_filename"] == "invoice_scan.pdf.exe"
    assert meta["signature_analysis"]["signature_detected"] is True
    assert "Portable Executable" in meta["signature_analysis"]["signature_name"]

    # Verify investigative indicators
    rule_names = [ind["rule"] for ind in meta["investigative_indicators"]]
    assert "SUSPICIOUS_DOUBLE_EXTENSION" in rule_names
    assert "EXECUTABLE_PAYLOAD_TYPE" in rule_names
