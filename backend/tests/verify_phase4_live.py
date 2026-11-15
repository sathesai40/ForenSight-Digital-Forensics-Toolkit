"""Phase 4 Live Integration, Forensic Integrity, and Security Verification Script.

Tests the live ForenSight services against http://127.0.0.1:8000.
"""

import sys
import io
import os
import stat
import hashlib
import json
import httpx
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_live_workflow():
    print("=" * 70)
    print("STARTING PHASE 4 END-TO-END VERIFICATION ON " + BASE_URL)
    print("=" * 70)

    with httpx.Client(base_url=BASE_URL, timeout=30.0, follow_redirects=True) as client:
        # 1. Health Check
        print("\n[STEP 1] Testing /api/health and environment diagnostics...")
        res = client.get("/api/health")
        assert res.status_code == 200, f"Health check failed: {res.status_code} {res.text}"
        health_data = res.json()
        assert health_data["status"] == "healthy"
        assert health_data["database_connected"] is True
        assert health_data["vault_ready"] is True
        print(f" -> OK: System Healthy, DB Connected, Vault Ready. Storage free: {health_data['diagnostics']['free_storage_bytes']} bytes")

        # 2. Case Creation
        print("\n[STEP 2] Creating new investigation: 'Unauthorized Access Investigation'...")
        case_payload = {
            "title": "Unauthorized Access Investigation",
            "description": "Investigation into brute-force authentication attempts and unauthorized privilege escalation.",
            "investigator_name": "Special Agent J. Vance",
            "priority": "HIGH"
        }
        res = client.post("/api/v1/cases", json=case_payload)
        assert res.status_code == 201, f"Failed to create case: {res.status_code} {res.text}"
        case = res.json()
        case_id = case["id"]
        case_number = case["case_number"]
        assert case["title"] == "Unauthorized Access Investigation"
        assert case["status"] == "OPEN"
        assert case["priority"] == "HIGH"
        print(f" -> OK: Created Case ID {case_id} ({case_number}) - Status: {case['status']}, Priority: {case['priority']}")

        # 3. Update Status and Priority
        print("\n[STEP 3] Updating case status to IN_PROGRESS and priority to CRITICAL...")
        update_payload = {
            "status": "IN_PROGRESS",
            "priority": "CRITICAL"
        }
        res = client.patch(f"/api/v1/cases/{case_id}?operator=Special%20Agent%20J.%20Vance", json=update_payload)
        assert res.status_code == 200, f"Failed to update case: {res.status_code} {res.text}"
        updated_case = res.json()
        assert updated_case["status"] == "IN_PROGRESS"
        assert updated_case["priority"] == "CRITICAL"
        print(f" -> OK: Updated Case Status={updated_case['status']}, Priority={updated_case['priority']}")

        # 4. Upload Sample Evidence
        print("\n[STEP 4] Uploading synthetic evidence file (sample_evidence.bin)...")
        evidence_content = b"FORENSIGHT_SYNTHETIC_EVIDENCE_DUMP_V1\nAcquisition Source: host-sec01:/var/log/audit.slice\nPayload: 5365637572697479417564697444756d705665726966696564\n"
        expected_sha256 = hashlib.sha256(evidence_content).hexdigest()

        files = {"file": ("sample_evidence.bin", evidence_content, "application/octet-stream")}
        data = {
            "investigator_name": "Special Agent J. Vance",
            "chain_of_custody_notes": "Acquired live system memory and audit slice from host-sec01"
        }
        res = client.post(f"/api/v1/cases/{case_id}/evidence", data=data, files=files)
        assert res.status_code == 201, f"Failed to upload evidence: {res.status_code} {res.text}"
        evidence = res.json()
        evidence_id = evidence["id"]
        assert evidence["sha256_hash"] == expected_sha256
        assert evidence["integrity_status"] == "VERIFIED"
        assert not evidence["file_path"].startswith("D:"), "Absolute paths must not be exposed in API!"
        assert "vault" in evidence["file_path"], f"Unexpected relative path: {evidence['file_path']}"
        print(f" -> OK: Uploaded Evidence ID {evidence_id}, SHA256: {evidence['sha256_hash']}")

        # 5. Extract File Metadata
        print("\n[STEP 5] Extracting evidence metadata and forensic indicators...")
        res = client.get(f"/api/v1/evidence/{evidence_id}/metadata")
        assert res.status_code == 200, f"Failed to extract metadata: {res.status_code} {res.text}"
        meta = res.json()
        assert meta["source_metadata"]["sha256_hash"] == expected_sha256
        assert meta["vault_storage_metadata"]["actual_size_bytes"] == len(evidence_content)
        assert "investigative_indicators" in meta
        print(f" -> OK: Metadata extracted. Size: {meta['vault_storage_metadata']['actual_size_bytes']} bytes, MIME: {meta['source_metadata']['declared_mime_type']}, Indicators: {len(meta['investigative_indicators'])}")

        # 6. Verify SHA-256 Hash
        print("\n[STEP 6] Recalculating and verifying SHA-256 hash...")
        res = client.post(f"/api/v1/evidence/{evidence_id}/verify?operator=Special%20Agent%20J.%20Vance")
        assert res.status_code == 200, f"Verification failed: {res.status_code} {res.text}"
        verify_result = res.json()
        assert verify_result["status"] == "MATCH"
        assert verify_result["calculated_sha256"] == expected_sha256
        assert verify_result["expected_sha256"] == expected_sha256
        print(f" -> OK: Integrity Status: {verify_result['status']} (Recorded == Calculated)")

        # 7. Import Synthetic Authentication Logs
        print("\n[STEP 7] Importing synthetic authentication logs with brute force and escalation...")
        auth_log = (
            "2026-11-15T02:00:10.000Z host-sec01 sshd[20101]: Failed password for invalid user admin from 198.51.100.99 port 41201 ssh2\n"
            "2026-11-15T02:00:15.000Z host-sec01 sshd[20102]: Failed password for invalid user root from 198.51.100.99 port 41202 ssh2\n"
            "2026-11-15T02:00:21.000Z host-sec01 sshd[20103]: Failed password for invalid user operator from 198.51.100.99 port 41203 ssh2\n"
            "2026-11-15T02:00:26.000Z host-sec01 sshd[20104]: Failed password for invalid user svc_backup from 198.51.100.99 port 41204 ssh2\n"
            "2026-11-15T02:00:32.000Z host-sec01 sshd[20105]: Failed password for invalid user forensic from 198.51.100.99 port 41205 ssh2\n"
            "2026-11-15T02:00:45.000Z host-sec01 sshd[20110]: Accepted password for svc_backup from 198.51.100.99 port 41210 ssh2\n"
            "2026-11-15T02:01:05.000Z host-sec01 sudo: svc_backup : TTY=pts/1 ; PWD=/home/svc_backup ; USER=root ; COMMAND=/bin/bash\n"
        )
        files = {"file": ("auth.log", auth_log.encode("utf-8"), "text/plain")}
        data = {
            "operator": "Special Agent J. Vance"
        }
        res = client.post(f"/api/v1/cases/{case_id}/logs/analyze", data=data, files=files)
        assert res.status_code == 201, f"Failed to analyze logs: {res.status_code} {res.text}"
        log_res = res.json()
        assert log_res["events_stored"] > 0
        rule_ids = [f["rule"] for f in log_res["findings"]]
        print(f" -> OK: Log analysis complete. Events stored: {log_res['events_stored']}, Rules triggered: {rule_ids}")
        assert "BRUTE_FORCE_IP_THRESHOLD" in rule_ids, "Expected BRUTE_FORCE_IP_THRESHOLD rule trigger"
        assert "BRUTE_FORCE_SUCCESS_SEQUENCE" in rule_ids, "Expected BRUTE_FORCE_SUCCESS_SEQUENCE rule trigger"

        # 8. Investigation Timeline
        print("\n[STEP 8] Verifying Investigation Timeline correlation...")
        res = client.get(f"/api/v1/cases/{case_id}/timeline")
        assert res.status_code == 200, f"Failed to get timeline: {res.status_code} {res.text}"
        timeline = res.json()
        assert timeline["total_events"] > 0
        categories = {item["category"] for item in timeline["timeline"]}
        print(f" -> OK: Timeline returned {timeline['total_events']} events. Categories present: {categories}")
        assert "EVIDENCE_ACQUISITION" in categories
        assert "SECURITY_EVENT" in categories
        assert "AUDIT_ACTION" in categories

        # 9. Audit Trail
        print("\n[STEP 9] Checking Audit Trail integrity...")
        res = client.get(f"/api/v1/audit?case_id={case_id}")
        assert res.status_code == 200, f"Failed to get audit: {res.status_code} {res.text}"
        audit_records = res.json()
        actions = [a["action"] for a in audit_records]
        print(f" -> OK: Audit trail recorded {len(audit_records)} actions: {actions}")
        assert "CASE_CREATED" in actions
        assert "STATUS_CHANGED" in actions
        assert "EVIDENCE_ACQUIRED" in actions
        assert "INTEGRITY_VERIFIED" in actions
        assert "LOGS_ANALYZED" in actions

        # 10. Dashboard Statistics Verification
        print("\n[STEP 10] Verifying Dashboard statistics...")
        res = client.get("/api/v1/dashboard/stats")
        assert res.status_code == 200, f"Failed to get dashboard stats: {res.status_code} {res.text}"
        dash = res.json()
        assert dash["total_cases"] >= 1
        assert dash["total_evidence"] >= 1
        assert dash["total_events"] >= 1
        assert "HIGH" in dash["events_by_severity"] or "CRITICAL" in dash["events_by_severity"]
        print(f" -> OK: Dashboard Stats: Total Cases={dash['total_cases']}, Total Evidence={dash['total_evidence']}, Total Events={dash['total_events']}, Severities={dash['events_by_severity']}")

        # 11. PDF Report Export & Inspection
        print("\n[STEP 11] Generating & downloading forensic PDF report...")
        res = client.get(f"/api/v1/cases/{case_id}/report/pdf?operator=Special%20Agent%20J.%20Vance")
        assert res.status_code == 200, f"Failed to export report: {res.status_code} {res.text}"
        assert res.headers["content-type"] == "application/pdf"
        pdf_bytes = res.content
        assert pdf_bytes.startswith(b"%PDF-1.4"), "Generated file does not start with %PDF-1.4 header!"
        assert len(pdf_bytes) > 5000, f"PDF file size is unexpectedly small: {len(pdf_bytes)} bytes"
        
        # Decompress ASCII85 / Flate streams to inspect PDF text content
        import base64
        import zlib
        import re
        stream_matches = re.findall(rb'stream\r?\n(.*?)endstream', pdf_bytes, re.DOTALL)
        pdf_decompressed_text = ""
        for s in stream_matches:
            if b'~>' in s:
                try:
                    raw = base64.a85decode(s.strip(), adobe=True)
                    pdf_decompressed_text += zlib.decompress(raw).decode('latin1', errors='ignore') + "\n"
                except Exception as e:
                    pass

        assert case_number in pdf_decompressed_text, f"Case number {case_number} missing from PDF!"
        assert "Unauthorized Access Investigation" in pdf_decompressed_text, "Case title missing from PDF!"
        assert expected_sha256[:16] in pdf_decompressed_text, "Evidence SHA-256 hash prefix missing from PDF!"
        assert "CRITICAL SEQUENCE" in pdf_decompressed_text or "198.51.100.99" in pdf_decompressed_text, "Security findings missing from PDF!"
        assert "EVIDENTIARY DISCLAIMER" in pdf_decompressed_text, "Forensic methodology statement missing!"
        print(f" -> OK: PDF inspected successfully. Valid %PDF-1.4, length={len(pdf_bytes)} bytes, contains Case Number ({case_number}), SHA256, Findings, and Integrity Statement.")

        # 12. Security & Edge-Case Testing (Task 4)
        print("\n[STEP 12] Running Security & Edge Case Tests...")

        # 404 for invalid case ID
        res = client.get("/api/v1/cases/999999")
        assert res.status_code == 404, f"Expected 404 for invalid case, got {res.status_code}"
        print(" -> OK: Non-existent case ID properly returns 404.")

        # Upload reject for oversized file (> 25MB)
        oversized_data = b"X" * (26 * 1024 * 1024)
        res = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            data={"investigator_name": "Examiner"},
            files={"file": ("bigfile.bin", oversized_data, "application/octet-stream")}
        )
        assert res.status_code == 413, f"Expected 413 for oversized file, got {res.status_code}"
        print(" -> OK: Oversized evidence (>25MB) rejected with HTTP 413.")

        # Directory traversal sanitization in evidence upload
        traversal_files = {"file": ("../../../../etc/shadow", b"dummy root hash", "text/plain")}
        res = client.post(
            f"/api/v1/cases/{case_id}/evidence",
            data={"investigator_name": "Examiner"},
            files=traversal_files
        )
        assert res.status_code == 201, f"Failed traversal upload test: {res.status_code}"
        traversal_evidence = res.json()
        assert not traversal_evidence["file_path"].startswith(".."), "Stored path should not contain parent traversals!"
        assert "shadow" in traversal_evidence["stored_filename"]
        print(" -> OK: Path traversal attack in filename safely sanitized.")

        # Hash tampering detection (MISMATCH)
        disk_path = Path("D:/ForenSight/backend/data/vault") / traversal_evidence["stored_filename"]
        if disk_path.exists():
            os.chmod(disk_path, stat.S_IWRITE | stat.S_IREAD)
            with open(disk_path, "wb") as f:
                f.write(b"TAMPERED_BYTES_REPLACED")
            os.chmod(disk_path, stat.S_IREAD)

            res = client.post(f"/api/v1/evidence/{traversal_evidence['id']}/verify?operator=Examiner")
            assert res.status_code == 200
            mismatch_data = res.json()
            assert mismatch_data["status"] == "MISMATCH", f"Expected MISMATCH, got {mismatch_data['status']}"
            print(" -> OK: Tampered evidence bytes successfully detected with status MISMATCH.")

        # Missing evidence file on disk returns status ERROR
        temp_files = {"file": ("vanished.bin", b"temporary bytes", "application/octet-stream")}
        res = client.post(f"/api/v1/cases/{case_id}/evidence", data={"investigator_name": "Examiner"}, files=temp_files)
        assert res.status_code == 201
        vanished_evidence = res.json()
        vanished_path = Path("D:/ForenSight/backend/data/vault") / vanished_evidence["stored_filename"]
        if vanished_path.exists():
            os.chmod(vanished_path, stat.S_IWRITE)
            os.remove(vanished_path)
        
        res = client.post(f"/api/v1/evidence/{vanished_evidence['id']}/verify?operator=Examiner")
        assert res.status_code == 200
        vanished_res = res.json()
        assert vanished_res["status"] == "ERROR", f"Expected ERROR for missing evidence file, got {vanished_res['status']}"
        print(" -> OK: Missing evidence file on disk properly returns status ERROR.")

        # Non-existent evidence record ID returns 404
        missing_fake_id = 999999
        res = client.post(f"/api/v1/evidence/{missing_fake_id}/verify?operator=Examiner")
        assert res.status_code == 404
        print(" -> OK: Non-existent evidence record ID returns 404.")

        # Malformed log file handling
        res = client.post(
            f"/api/v1/cases/{case_id}/logs/analyze",
            data={"operator": "Examiner"},
            files={"file": ("corrupted.bin", b"\x00\xff\xfe\x01\x02", "application/octet-stream")}
        )
        assert res.status_code in [200, 201, 400, 422], f"Unexpected response on corrupted log: {res.status_code}"
        print(f" -> OK: Corrupted binary log handled safely without crash (Status: {res.status_code}).")

    print("\n" + "=" * 70)
    print("ALL PHASE 4 WORKFLOW & SECURITY INTEGRATION TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_live_workflow()
