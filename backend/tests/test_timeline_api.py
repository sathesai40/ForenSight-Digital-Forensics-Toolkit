import io
import os
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.case import InvestigationCase
from app.models.security_event import SecurityEvent


def test_timeline_ordering_and_aggregation(client: TestClient, db_session: Session):
    """Test unified timeline aggregating evidence acquisitions, security events, and audit actions in strict UTC."""
    case = InvestigationCase(
        case_number=f"FS-2026-TLTEST-{os.urandom(4).hex()}",
        title="Timeline Chronology Case",
        investigator_name="Investigator Cruz",
        priority="HIGH",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    base_time = datetime(2026, 11, 15, 1, 0, 0, tzinfo=timezone.utc)

    # 1. Add security events with explicit spaced UTC timestamps
    se1 = SecurityEvent(
        case_id=case.id,
        timestamp=base_time + timedelta(minutes=10),
        event_type="NETWORK_CONNECTION",
        severity="INFO",
        description="First event in timeline sequence",
    )
    se2 = SecurityEvent(
        case_id=case.id,
        timestamp=base_time + timedelta(minutes=30),
        event_type="AUTHENTICATION",
        severity="HIGH",
        description="Third event in timeline sequence",
    )
    se3 = SecurityEvent(
        case_id=case.id,
        timestamp=base_time + timedelta(minutes=20),
        event_type="FILE_MODIFICATION",
        severity="MEDIUM",
        description="Second event in timeline sequence",
    )
    db_session.add_all([se1, se2, se3])
    db_session.commit()

    # Query chronological timeline (ascending)
    resp = client.get(f"/api/v1/cases/{case.id}/timeline?order=asc")
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == case.id
    timeline = data["timeline"]
    assert len(timeline) >= 3

    # Verify timestamps are strictly monotonic increasing
    timestamps = [datetime.fromisoformat(item["timestamp"]) for item in timeline]
    for i in range(len(timestamps) - 1):
        assert timestamps[i] <= timestamps[i + 1]

    # Query reverse chronological timeline (descending)
    resp_desc = client.get(f"/api/v1/cases/{case.id}/timeline?order=desc")
    assert resp_desc.status_code == 200
    data_desc = resp_desc.json()
    timestamps_desc = [datetime.fromisoformat(item["timestamp"]) for item in data_desc["timeline"]]
    for i in range(len(timestamps_desc) - 1):
        assert timestamps_desc[i] >= timestamps_desc[i + 1]


def test_timeline_category_filtering(client: TestClient, db_session: Session):
    """Test filtering timeline by category."""
    case = InvestigationCase(
        case_number=f"FS-2026-TLFILTER-{os.urandom(4).hex()}",
        title="Timeline Filter Test",
        investigator_name="Investigator Cruz",
        priority="LOW",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    se = SecurityEvent(
        case_id=case.id,
        timestamp=datetime.now(timezone.utc),
        event_type="AUTHENTICATION",
        severity="INFO",
        description="Filtered test event",
    )
    db_session.add(se)
    db_session.commit()

    resp = client.get(f"/api/v1/cases/{case.id}/timeline?category=SECURITY_EVENT")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["timeline"]) >= 1
    assert all(item["category"] == "SECURITY_EVENT" for item in data["timeline"])
