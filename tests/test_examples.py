"""
Tests for example endpoints
"""

from fastapi.testclient import TestClient


def test_get_examples(client: TestClient):
    response = client.get("/raven-api/v1/examples/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_example(client: TestClient):
    example_data = {
        "name": "Test Example",
        "description": "This is a test example"
    }
    response = client.post("/raven-api/v1/examples/", json=example_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == example_data["name"]
    assert data["description"] == example_data["description"]
    assert "id" in data


def test_get_example_by_id(client: TestClient):
    # First create an example
    example_data = {
        "name": "Test Example for get_by_id",
        "description": "This is a test example"
    }
    create_response = client.post("/raven-api/v1/examples/", json=example_data)
    created_example = create_response.json()
    
    # Then get it by ID
    response = client.get(f"/raven-api/v1/examples/{created_example['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_example["id"]
    assert data["name"] == example_data["name"]
