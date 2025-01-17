import httpx
import pytest


@pytest.fixture(scope="module")
def client():
    return httpx.Client(base_url="http://localhost:8000")


def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the proxy service!"}


def test_list_pets(client):
    response = client.get("/pets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
