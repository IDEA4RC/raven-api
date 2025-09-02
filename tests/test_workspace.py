from fastapi.testclient import TestClient
from app.api.endpoints import workspace as ws_ep


def test_get_workspaces_ok(client: TestClient, monkeypatch):
    class FakeWS:
        id = 1
        name = "W"
        description = None
        data_access = 0
        creator_id = 1
        team_ids = []
        metadata_search = 0
        data_analysis = 0
        result_report = 0
        v6_study_id = None
        status = None
        creation_date = "2024-01-01T00:00:00Z"

    def fake_get_multi(db=None, skip=0, limit=100):
        return [FakeWS()]

    monkeypatch.setattr(ws_ep.workspace_service, "get_multi", fake_get_multi)
    r = client.get("/raven-api/v1/workspaces/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_workspace_404(client: TestClient, monkeypatch):
    def fake_get(db=None, id=None):
        return None

    monkeypatch.setattr(ws_ep.workspace_service, "get", fake_get)
    r = client.get("/raven-api/v1/workspaces/999")
    assert r.status_code == 404
