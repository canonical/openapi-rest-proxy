import sys
import os
import pytest
from fastapi.routing import APIRouter

os.environ["OPENAPI_SCHEMA_URL"] = "http://example.com/openapi.yaml"
os.environ["ORIGIN_BASE_URL"] = "http://example.com"

from proxy.proxy import (
    create_proxy_routes,
)


def test_create_proxy_routes():
    schema = {"paths": {"/pets": {"get": {}}, "/pets/{petId}": {"get": {}}}}
    origin_base_url = "http://example.com"

    router = APIRouter()
    create_proxy_routes(router, schema, origin_base_url)

    routes = [route.path for route in router.routes]
    assert "/pets" in routes
    assert "/pets/{petId}" in routes
