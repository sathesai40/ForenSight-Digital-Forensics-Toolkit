import io
import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.case import InvestigationCase
from app.models.security_event import SecurityEvent


def create_test_case(db_session: Session) -> InvestigationCase:
    case = InvestigationCase(
        case_number=f"FS-2026-LOGTEST-{os.urandom(4).hex()}",
        title="Log Ingestion & Analysis Test Case",
        investigator_name="Analyst Sterling",
        priority="HIGH",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


def test_auth_log_analysis_and_brute_force_detection(client: TestClient, db_session: Session):
    """Test parsing synthetic auth.log, detecting brute-force bursts and privilege escalation."""
    case = create_test_case(db_session)

    log_data = """
2026-11-15T01:14:02.000Z host-sec01 sshd[14221]: Failed password for invalid user root from 198.51.100.42 port 54312 ssh2
2026-11-15T01:14:05.000Z host-sec01 sshd[14223]: Failed password for invalid user admin from 198.51.100.42 port 54314 ssh2
2026-11-15T01:14:09.000Z host-sec01 sshd[14225]: Failed password for invalid user analyst from 198.51.100.42 port 54316 ssh2
2026-11-15T01:15:22.000Z host-sec01 sshd[14230]: Accepted publickey for forensic_user from 192.0.2.15 port 55102 ssh2: RSA SHA256:7f8e...
2026-11-15T01:16:01.000Z host-sec01 sudo: forensic_user : TTY=pts/0 ; PWD=/home/forensic_user ; USER=root ; COMMAND=/bin/journalctl -u ssh
""".strip()

    response = client.post(
        f"/api/v1/cases/{case.id}/logs/analyze",
        data={"content": log_data, "operator": "Analyst Sterling"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["case_id"] == case.id
    assert data["total_parsed"] == 5

    # Check that brute force from 198.51.100.42 was detected (3 failures)
    findings = data["findings"]
    assert len(findings) >= 1
    bf_finding = next((f for f in findings if f["rule"] == "BRUTE_FORCE_IP_THRESHOLD"), None)
    assert bf_finding is not None
    assert bf_finding["source_ip"] == "198.51.100.42"
    assert bf_finding["failure_count"] == 3

    # Check persisted SecurityEvent records in DB
    events = db_session.query(SecurityEvent).filter(SecurityEvent.case_id == case.id).all()
    assert len(events) >= 5

    # Verify sudo command was tagged as PRIVILEGE_ESCALATION
    sudo_ev = next((e for e in events if e.event_type == "PRIVILEGE_ESCALATION"), None)
    assert sudo_ev is not None
    assert "forensic_user" in sudo_ev.user_account
    assert "journalctl" in sudo_ev.description


def test_suspicious_sequence_detection(client: TestClient, db_session: Session):
    """Test high-confidence rule: brute-force attempts immediately followed by successful login."""
    case = create_test_case(db_session)

    log_data = """
2026-11-15T02:00:01.000Z host-sec01 sshd[100]: Failed password for user svc_admin from 203.0.113.88 port 41200 ssh2
2026-11-15T02:00:04.000Z host-sec01 sshd[101]: Failed password for user svc_admin from 203.0.113.88 port 41202 ssh2
2026-11-15T02:00:10.000Z host-sec01 sshd[102]: Accepted password for svc_admin from 203.0.113.88 port 41204 ssh2
""".strip()

    response = client.post(
        f"/api/v1/cases/{case.id}/logs/analyze",
        data={"content": log_data, "operator": "Analyst Sterling"},
    )
    assert response.status_code == 201
    data = response.json()

    # Verify that BRUTE_FORCE_SUCCESS_SEQUENCE was flagged as CRITICAL
    findings = data["findings"]
    seq_finding = next((f for f in findings if f["rule"] == "BRUTE_FORCE_SUCCESS_SEQUENCE"), None)
    assert seq_finding is not None
    assert seq_finding["severity"] == "CRITICAL"
    assert seq_finding["source_ip"] == "203.0.113.88"


def test_csv_log_import(client: TestClient, db_session: Session):
    """Test CSV log ingestion, header mapping, and UTC timestamp normalization."""
    case = create_test_case(db_session)

    csv_data = """timestamp,event_type,severity,source_ip,destination_ip,user_account,description
2026-11-15T03:00:00Z,NETWORK_CONNECTION,INFO,10.0.0.5,10.0.0.1,system,Outbound connection established
2026-11-15T03:05:00Z,PROCESS_EXECUTION,HIGH,10.0.0.5,,admin,Suspicious PowerShell encoded command execution
""".strip()

    response = client.post(
        f"/api/v1/cases/{case.id}/logs/analyze",
        files={"file": ("firewall_export.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        data={"operator": "Analyst Sterling"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total_parsed"] == 2

    # Query events list via API
    get_events_resp = client.get(f"/api/v1/cases/{case.id}/events")
    assert get_events_resp.status_code == 200
    events = get_events_resp.json()
    assert len(events) == 2
    assert any(e["event_type"] == "PROCESS_EXECUTION" for e in events)


def test_log_analyze_empty_or_missing_case(client: TestClient, db_session: Session):
    """Test validation errors on empty log content or invalid case ID."""
    case = create_test_case(db_session)

    # Non-existent case -> 404
    resp404 = client.post(
        "/api/v1/cases/999999/logs/analyze",
        data={"content": "some log line", "operator": "Analyst"},
    )
    assert resp404.status_code == 404

    # Empty content for existing case -> 400
    resp400 = client.post(
        f"/api/v1/cases/{case.id}/logs/analyze",
        data={"content": "   ", "operator": "Analyst"},
    )
    assert resp400.status_code == 400


def test_repeated_log_import_deduplication(client: TestClient, db_session: Session):
    """Verify that repeated log imports do not create unintended duplicate events or findings."""
    case = create_test_case(db_session)

    log_data = """
2026-11-15T04:00:01.000Z host-sec01 sshd[201]: Failed password for user student01 from 192.0.2.45 port 51201 ssh2
2026-11-15T04:00:04.000Z host-sec01 sshd[202]: Failed password for user student01 from 192.0.2.45 port 51202 ssh2
2026-11-15T04:00:07.000Z host-sec01 sshd[203]: Failed password for user student01 from 192.0.2.45 port 51203 ssh2
2026-11-15T04:00:10.000Z host-sec01 sshd[204]: Accepted password for student01 from 192.0.2.45 port 51204 ssh2
""".strip()

    # Initial import: 4 events parsed, 2 findings generated (brute force + success sequence)
    resp1 = client.post(
        f"/api/v1/cases/{case.id}/logs/analyze",
        data={"content": log_data, "operator": "Analyst Sterling"},
    )
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["total_parsed"] == 4
    initial_stored = data1["events_stored"]

    # Total events in DB after first import
    events_in_db_1 = db_session.query(SecurityEvent).filter(SecurityEvent.case_id == case.id).all()
    count_1 = len(events_in_db_1)
    assert count_1 == initial_stored

    # Re-import identical log stream
    resp2 = client.post(
        f"/api/v1/cases/{case.id}/logs/analyze",
        data={"content": log_data, "operator": "Analyst Sterling"},
    )
    assert resp2.status_code == 201
    data2 = resp2.json()

    # Verify that total DB records did NOT duplicate
    events_in_db_2 = db_session.query(SecurityEvent).filter(SecurityEvent.case_id == case.id).all()
    count_2 = len(events_in_db_2)
    assert count_2 == count_1, f"Expected {count_1} events but found {count_2} (duplicate events/findings created!)"

    # Verify finding counts remain unchanged
    findings_1 = [e for e in events_in_db_1 if e.event_type == "SUSPICIOUS_INDICATOR"]
    findings_2 = [e for e in events_in_db_2 if e.event_type == "SUSPICIOUS_INDICATOR"]
    assert len(findings_1) == len(findings_2)
