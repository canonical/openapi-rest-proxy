import os
import pytest
import respx
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from httpx import Request, Response

os.environ["OPENAPI_SCHEMA_URL"] = "http://localhost:8001/example-openapi.yml"
os.environ["ORIGIN_BASE_URL"] = "http://localhost:8001"
os.environ["ENDPOINT_ALLOW_LIST"] = "GET:/pets"
os.environ["FIXED_REQUEST_HEADERS"] = "X-Test-Header:TestValue"

from proxy.app import app
from httpx import AsyncClient

# Note! You need to have the schema server running at https://localhost:8001
# Easiest achieved with `docker-compose up schema -d` at the root of the project.


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "origin": "http://localhost:8001",
        "schema": "http://localhost:8001/example-openapi.yml",
    }


def test_list_pets_without_mocking(client):
    response = client.get("/pets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_pets_with_mocking(client):
    with respx.mock(base_url="http://localhost:8001") as mock:
        mock.get("/pets").mock(return_value=Response(status_code=200, json=[]))

        response = client.get("/pets")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

        assert mock.calls[0].request.url.path == "/pets"
        assert mock.calls[0].request.headers["X-Test-Header"] == "TestValue"
