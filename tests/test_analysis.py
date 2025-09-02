from fastapi.testclient import TestClient
from app.api.endpoints import analysis as a_ep


def test_get_analyses_ok(client: TestClient, monkeypatch):
    class FakeAnalysis:
        id = 1
        workspace_id = 1

    def fake_get_multi(db=None, skip=0, limit=100):
        return [FakeAnalysis()]

    monkeypatch.setattr(a_ep.analysis_service, "get_multi", fake_get_multi)
    r = client.get("/raven-api/v1/analyses/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_analysis_404(client: TestClient, monkeypatch):
    def fake_get(db=None, id=None):
        return None

    monkeypatch.setattr(a_ep.analysis_service, "get", fake_get)
    r = client.get("/raven-api/v1/analyses/999")
    assert r.status_code == 404
