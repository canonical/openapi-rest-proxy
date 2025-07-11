import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.routing import APIRouter

os.environ["OPENAPI_SCHEMA_URL"] = "http://example.com/openapi.yaml"
os.environ["ORIGIN_BASE_URL"] = "http://example.com"

from proxy.proxy import (
    create_proxy_routes,
    proxy,
)


def test_create_proxy_routes():
    schema = {"paths": {"/pets": {"get": {}}, "/pets/{petId}": {"get": {}}}}
    origin_base_url = "http://example.com"

    router = APIRouter()
    create_proxy_routes(router, schema, origin_base_url)

    routes = [route.path for route in router.routes]
    assert "/pets" in routes
    assert "/pets/{petId}" in routes


@pytest.mark.asyncio
async def test_proxy_with_path_parameters():
    """Test that path parameters are correctly substituted in the proxy URL."""
    mock_request = MagicMock(spec=Request)
    mock_request.path_params = {"petId": "123", "ownerId": "456"}
    mock_request.query_params = {}
    mock_request.headers = {"content-type": "application/json"}
    mock_request.body = AsyncMock(return_value=b"")

    with patch("proxy.proxy.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.text = '{"result": "success"}'
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}

        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        await proxy(
            request=mock_request,
            method="GET",
            path="/pets/{petId}/owners/{ownerId}",
            origin_base_url="http://example.com",
        )

        mock_client.return_value.__aenter__.return_value.request.assert_called_once()
        call_args = mock_client.return_value.__aenter__.return_value.request.call_args
        assert call_args[1]["url"] == "http://example.com/pets/123/owners/456"


@pytest.mark.asyncio
async def test_proxy_without_path_parameters():
    """Test that paths without parameters work correctly."""
    mock_request = MagicMock(spec=Request)
    mock_request.path_params = {}
    mock_request.query_params = {}
    mock_request.headers = {"content-type": "application/json"}
    mock_request.body = AsyncMock(return_value=b"")

    with patch("proxy.proxy.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.text = '{"result": "success"}'
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}

        mock_client.return_value.__aenter__.return_value.request = AsyncMock(
            return_value=mock_response
        )

        await proxy(
            request=mock_request,
            method="GET",
            path="/pets",
            origin_base_url="http://example.com",
        )

        mock_client.return_value.__aenter__.return_value.request.assert_called_once()
        call_args = mock_client.return_value.__aenter__.return_value.request.call_args
        assert call_args[1]["url"] == "http://example.com/pets"
