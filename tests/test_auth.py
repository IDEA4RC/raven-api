from fastapi.testclient import TestClient
import types

from app.services import auth as auth_module


def test_login_success(client: TestClient, monkeypatch):
    def fake_authenticate(username, password):
        return {"access_token": "fake-token", "token_type": "bearer"}

    monkeypatch.setattr(auth_module.AuthService, "authenticate", staticmethod(fake_authenticate))
    # Also stub keycloak validation used in endpoint
    from app.utils import keycloak as keycloak_module

    def fake_validate_token(token: str):
        return {"sub": "fake-sub", "email": "u@example.com"}

    monkeypatch.setattr(keycloak_module.keycloak_handler, "validate_token", fake_validate_token)

    r = client.post("/raven-api/v1/auth/login", data={"username": "u", "password": "p"})
    assert r.status_code == 200
    assert r.json()["access_token"] == "fake-token"


def test_refresh_token_success(client: TestClient, monkeypatch):
    def fake_refresh(refresh_token):
        return {"access_token": "new-token", "token_type": "bearer"}

    monkeypatch.setattr(auth_module.AuthService, "refresh_token", staticmethod(fake_refresh))
    r = client.post("/raven-api/v1/auth/refresh-token", params={"refresh_token": "rt"})
    assert r.status_code == 200
    assert r.json()["access_token"] == "new-token"
