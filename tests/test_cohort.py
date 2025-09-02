from fastapi.testclient import TestClient
from app.api.endpoints import cohort as c_ep


def test_get_cohorts_ok(client: TestClient, monkeypatch):
    class FakeCohort:
        id = 1
        workspace_id = 1

    def fake_get_all(db=None, skip=0, limit=100):
        return [FakeCohort()]

    monkeypatch.setattr(c_ep.cohort_service, "get_all_cohorts", fake_get_all)
    r = client.get("/raven-api/v1/cohorts/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_cohort_404(client: TestClient, monkeypatch):
    def fake_get_by_id(db=None, cohort_id=None):
        return None

    monkeypatch.setattr(c_ep.cohort_service, "get_cohort_by_id", fake_get_by_id)
    r = client.get("/raven-api/v1/cohorts/999")
    assert r.status_code == 404
