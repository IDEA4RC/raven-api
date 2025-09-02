"""
Test configuration
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path for `import app`
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from main import app
from app.api.deps import get_current_user as real_get_current_user, get_db as deps_get_db


class FakeQuery:
    def __init__(self, model):
        self.model = model

    # Chainable no-ops
    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def offset(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    # Results
    def all(self):
        return []

    def first(self):
        return None


class FakeSession:
    def query(self, model):
        return FakeQuery(model)

    def add(self, obj):
        return None

    def commit(self):
        return None

    def refresh(self, obj):
        return None

    def flush(self):
        return None

    def close(self):
        return None


def override_get_db():
    # Yield a fake session that supports the minimal API used in endpoints
    yield FakeSession()


@pytest.fixture()
def test_db():
    # No-op fixture to keep compatibility with existing tests
    yield


def _fake_user():
    class U:
        id = 1
        keycloak_id = "fake-sub"
        username = "testuser"
        email = "test@example.com"
        first_name = "Test"
        last_name = "User"
        is_active = True
        user_type_id = None

    return U()


@pytest.fixture()
def client(test_db):
    # Override dependencies: DB and current user
    app.dependency_overrides[deps_get_db] = override_get_db
    app.dependency_overrides[real_get_current_user] = lambda: _fake_user()
    with TestClient(app) as c:
        yield c
    # Restore overrides
    app.dependency_overrides = {}
