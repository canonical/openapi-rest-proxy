import httpx
import yaml
import logging
import argparse
import os

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute

from .proxy import create_proxy_routes, filter_endpoints

app = FastAPI()

logger = logging.getLogger()
logger.name = "openapi-rest-proxy"

logging.basicConfig(level=logging.DEBUG)


def load_openapi_schema(url: str):
    logging.debug(f"Loading OpenAPI schema from {url}")
    response = httpx.get(url)
    response.raise_for_status()
    schema = yaml.safe_load(response.text)
    logging.debug(f"Loaded OpenAPI schema.")
    return schema


openapi_schema_url = os.getenv("OPENAPI_SCHEMA_URL")
origin_base_url = os.getenv("ORIGIN_BASE_URL")
port = int(os.getenv("PORT", 8000))
host = os.getenv("HOST", "0.0.0.0")

if not openapi_schema_url or not origin_base_url:
    raise ValueError(
        "Environment variables OPENAPI_SCHEMA_URL and ORIGIN_BASE_URL must be set"
    )

openapi_schema = load_openapi_schema(openapi_schema_url)

# Example: ALLOW_LIST="GET:/pets|GET:/pets/{petId}"
allow_list = os.getenv("ENDPOINT_ALLOW_LIST", "").split("|")

if allow_list:
    logging.info(f"Filtering API to allow list: {allow_list}")
    openapi_schema = filter_endpoints(openapi_schema, allow_list)
else:
    logging.info("No allow list provided. Proxying all endpoints.")

create_proxy_routes(app.router, openapi_schema, origin_base_url=origin_base_url)


@app.get("/")
def read_root():
    return {"message": "Welcome to the proxy service!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=host, port=port)
