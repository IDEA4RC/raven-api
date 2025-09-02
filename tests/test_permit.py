from fastapi.testclient import TestClient
from app.api.endpoints import permit as p_ep


def test_get_permits_ok(client: TestClient, monkeypatch):
    class FakePermit:
        id = 1
        workspace_id = 1
        status = 0
        team_ids = []

    def fake_get_multi(db=None, skip=0, limit=100):
        return [FakePermit()]

    monkeypatch.setattr(p_ep.permit_service, "get_multi", fake_get_multi)
    r = client.get("/raven-api/v1/permits/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_permit_404(client: TestClient, monkeypatch):
    def fake_get(db=None, id=None):
        return None

    monkeypatch.setattr(p_ep.permit_service, "get", fake_get)
    r = client.get("/raven-api/v1/permits/999")
    assert r.status_code == 404
