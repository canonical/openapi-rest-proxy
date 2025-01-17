import os
import pytest
from fastapi.testclient import TestClient

os.environ["OPENAPI_SCHEMA_URL"] = "http://localhost:8001/example-openapi.yml"
os.environ["ORIGIN_BASE_URL"] = "http://localhost:8001"
os.environ["ENDPOINT_ALLOW_LIST"] = "GET:/pets"

from proxy.service import app

# Note! You need to have the schema server running at https://localhost:8001
# Easiest achieved with `docker-compose up schema -d` at the root of the project.


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the proxy service!"}


def test_list_pets(client):
    response = client.get("/pets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
