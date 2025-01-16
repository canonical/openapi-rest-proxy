import sys
import os
import pytest
from fastapi.testclient import TestClient
from httpx import Response
from unittest.mock import patch, AsyncMock

os.environ["OPENAPI_SCHEMA_URL"] = "http://example.com/openapi.yaml"
os.environ["ORIGIN_BASE_URL"] = "http://example.com"


from proxy.service import (
    app,
    load_openapi_schema,
    filter_endpoints,
    create_proxy_routes,
    proxy,
)

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the proxy service!"}


@patch("httpx.get")
def test_load_openapi_schema(mock_get):
    mock_response = Response(
        200, text="openapi: 3.0.0\ninfo:\n  title: Test API\npaths: {}"
    )
    mock_get.return_value = mock_response

    url = "http://example.com/openapi.yaml"
    schema = load_openapi_schema(url)
    assert schema["openapi"] == "3.0.0"
    assert schema["info"]["title"] == "Test API"


def test_filter_endpoints():
    schema = {"paths": {"/pets": {"get": {}}, "/pets/{petId}": {"get": {}, "post": {}}}}
    allow_list = ["GET:/pets", "GET:/pets/{petId}"]
    filtered_schema = filter_endpoints(schema, allow_list)
    assert "/pets" in filtered_schema["paths"]
    assert "get" in filtered_schema["paths"]["/pets"]
    assert "/pets/{petId}" in filtered_schema["paths"]
    assert "get" in filtered_schema["paths"]["/pets/{petId}"]
    assert "post" not in filtered_schema["paths"]["/pets/{petId}"]


@pytest.mark.asyncio
@patch("httpx.AsyncClient.request", new_callable=AsyncMock)
async def test_proxy(mock_request):
    mock_response = Response(200, content=b"{}")
    mock_request.return_value = mock_response

    request = client.build_request("GET", "/pets")
    response = await proxy(request, "GET", "/pets", "http://example.com")
    assert response.status_code == 200
    assert response.content == b"{}"


def test_create_proxy_routes():
    schema = {"paths": {"/pets": {"get": {}}, "/pets/{petId}": {"get": {}}}}
    origin_base_url = "http://example.com"
    create_proxy_routes(schema, origin_base_url)

    routes = [route.path for route in app.routes]
    assert "/pets" in routes
    assert "/pets/{petId}" in routes
