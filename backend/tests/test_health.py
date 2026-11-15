from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test the root index endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "ForenSight" in data["name"]
    assert data["status"] == "ONLINE"


def test_api_health_endpoint(client: TestClient):
    """Test the required GET /api/health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ["healthy", "degraded"]
    assert data["app_name"] == "ForenSight Digital Forensics Toolkit"
    assert data["version"] == "0.1.0"
    assert data["database_connected"] is True
    assert "timestamp" in data
    assert "diagnostics" in data
    assert data["diagnostics"]["database"] == "sqlite"


def test_api_v1_health_endpoint(client: TestClient):
    """Test the versioned GET /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["database_connected"] is True
