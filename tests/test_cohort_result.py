from fastapi.testclient import TestClient
from app.api.endpoints import cohort_result as cr_ep


def test_get_cohort_results_by_cohort_ok(client: TestClient, monkeypatch):
    class FakeCR:
        cohort_id = 1
        data_id = ["a"]

    def fake_get_by_cohort(db=None, cohort_id=None, skip=0, limit=100):
        return [FakeCR()]

    monkeypatch.setattr(cr_ep.cohort_result_service, "get_by_cohort", fake_get_by_cohort)
    r = client.get("/raven-api/v1/cohort-results/cohort/1")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_count_cohort_results_ok(client: TestClient, monkeypatch):
    def fake_count(db=None, cohort_id=None):
        return 3

    monkeypatch.setattr(cr_ep.cohort_result_service, "count_results_for_cohort", fake_count)
    r = client.get("/raven-api/v1/cohort-results/cohort/1/count")
    assert r.status_code == 200
    assert r.json() == 3
