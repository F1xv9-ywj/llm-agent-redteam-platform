from fastapi.testclient import TestClient

from redsentinel.app import create_app


def test_api_contract_and_authorization(tmp_path):
    client = TestClient(create_app(tmp_path / "api.db"))
    assert client.get("/health").json()["offline_default"] is True
    assert len(client.get("/api/cases").json()) >= 6
    assert client.post("/api/scans", json={"provider": "mock"}).status_code == 403
    response = client.post("/api/scans", json={"provider": "mock", "authorized": True})
    assert response.status_code == 201
    run = response.json()
    assert client.get(f"/api/runs/{run['id']}").json()["id"] == run["id"]
    assert client.get("/api/runs/missing").status_code == 404
