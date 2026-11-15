from fastapi.testclient import TestClient


def test_create_and_list_cases(client: TestClient):
    """Test creating a case and listing cases via API."""
    payload = {
        "title": "Suspected Credential Dumping",
        "description": "LSASS memory access attempts detected on domain controller.",
        "investigator_name": "Senior Investigator Ray",
        "lead_analyst": "Analyst Vance",
        "priority": "HIGH",
    }
    create_resp = client.post("/api/v1/cases", json=payload)
    assert create_resp.status_code == 201
    case_data = create_resp.json()
    assert case_data["title"] == payload["title"]
    assert case_data["status"] == "OPEN"
    assert "FS-" in case_data["case_number"]

    # Verify listing includes the case
    list_resp = client.get("/api/v1/cases")
    assert list_resp.status_code == 200
    cases = list_resp.json()
    assert len(cases) >= 1
    assert any(c["id"] == case_data["id"] for c in cases)

    # Verify audit record was created
    audit_resp = client.get(f"/api/v1/audit?case_id={case_data['id']}")
    assert audit_resp.status_code == 200
    audits = audit_resp.json()
    assert len(audits) >= 1
    assert audits[0]["action"] == "CASE_CREATED"
