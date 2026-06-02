"""
Tests for the /available_organizations endpoint and the organization filtering logic.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _org_response(orgs: list[dict]) -> MagicMock:
    """Fake httpx response for GET /organization."""
    r = MagicMock()
    r.raise_for_status = MagicMock()
    r.json.return_value = {"data": orgs}
    return r


def _node_response(nodes: list[dict]) -> MagicMock:
    """Fake httpx response for GET /node."""
    r = MagicMock()
    r.raise_for_status = MagicMock()
    r.json.return_value = {"data": nodes}
    return r


ALL_ORGS = [
    {"id": 1, "name": "UPM"},
    {"id": 5, "name": "INT"},
    {"id": 9, "name": "OUS"},
    {"id": 99, "name": "UNKNOWN_ORG"},   # not in whitelist
]


# ---------------------------------------------------------------------------
# Unit tests for _get_organizations filtering logic
# ---------------------------------------------------------------------------

class TestGetOrganizationsFiltering:

    def _make_service(self):
        from app.services.vantage_6 import Vantage6Service
        return Vantage6Service()

    def _mock_client(self, org_ids_online: list[int]):
        """
        Returns a context-manager mock for httpx.Client whose .get() returns
        the correct fake response based on the URL being called.
        """
        nodes = [
            {"organization": {"id": oid}, "status": "online"}
            for oid in org_ids_online
        ]

        client_instance = MagicMock()
        client_instance.__enter__ = MagicMock(return_value=client_instance)
        client_instance.__exit__ = MagicMock(return_value=False)

        def fake_get(url, **kwargs):
            if "/organization" in url:
                return _org_response(ALL_ORGS)
            if "/node" in url:
                return _node_response(nodes)
            raise ValueError(f"Unexpected URL: {url}")

        client_instance.get = MagicMock(side_effect=fake_get)
        return client_instance

    def test_returns_only_whitelisted_online_orgs(self):
        """Only orgs in ORGANIZATION_IDS={1,5,9} AND online should be returned."""
        svc = self._make_service()
        mock_client = self._mock_client(org_ids_online=[1, 9])   # INT (5) offline

        with patch("app.services.vantage_6.httpx.Client", return_value=mock_client):
            result = svc._get_organizations(access_token="tok", collaboration_id=3)

        assert set(result.keys()) == {1, 9}
        assert result[1] == "UPM"
        assert result[9] == "OUS"

    def test_unknown_org_excluded_even_if_online(self):
        """Org 99 is online but not in whitelist — must be excluded."""
        svc = self._make_service()
        mock_client = self._mock_client(org_ids_online=[1, 5, 9, 99])

        with patch("app.services.vantage_6.httpx.Client", return_value=mock_client):
            result = svc._get_organizations(access_token="tok", collaboration_id=3)

        assert 99 not in result
        assert set(result.keys()) == {1, 5, 9}

    def test_all_offline_returns_empty(self):
        """When no node is online, result should be empty."""
        svc = self._make_service()
        mock_client = self._mock_client(org_ids_online=[])

        with patch("app.services.vantage_6.httpx.Client", return_value=mock_client):
            result = svc._get_organizations(access_token="tok", collaboration_id=3)

        assert result == {}

    def test_get_available_organizations_shape(self):
        """get_available_organizations returns list of {id, name} dicts."""
        svc = self._make_service()
        mock_client = self._mock_client(org_ids_online=[1, 9])

        with patch("app.services.vantage_6.httpx.Client", return_value=mock_client):
            result = svc.get_available_organizations(access_token="tok")

        assert isinstance(result, list)
        ids = {item["id"] for item in result}
        assert ids == {1, 9}
        for item in result:
            assert "id" in item and "name" in item


# ---------------------------------------------------------------------------
# Integration test: endpoint returns 200 and correct shape
# ---------------------------------------------------------------------------

def test_available_organizations_endpoint_returns_200(client: TestClient):
    """
    The endpoint should respond 200 and return a list.
    V6 calls are mocked so no real network needed.
    """
    from app.api.deps import get_current_user_with_token as real_dep
    from main import app

    nodes = [{"organization": {"id": 1}, "status": "online"}]
    orgs = [{"id": 1, "name": "UPM"}, {"id": 5, "name": "INT"}]

    client_instance = MagicMock()
    client_instance.__enter__ = MagicMock(return_value=client_instance)
    client_instance.__exit__ = MagicMock(return_value=False)

    def fake_get(url, **kwargs):
        r = MagicMock()
        r.raise_for_status = MagicMock()
        if "/organization" in url:
            r.json.return_value = {"data": orgs}
        else:
            r.json.return_value = {"data": nodes}
        return r

    client_instance.get = MagicMock(side_effect=fake_get)

    class FakeUserCtx:
        class user:
            id = 1
        access_token = "fake"

    app.dependency_overrides[real_dep] = lambda: FakeUserCtx()

    with patch("app.services.vantage_6.httpx.Client", return_value=client_instance):
        r = client.get("/raven-api/v1/data-preparation/available_organizations")

    app.dependency_overrides.pop(real_dep, None)

    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    # Only UPM (online) should appear; INT is offline in this mock
    assert len(body) == 1
    assert body[0]["id"] == 1
