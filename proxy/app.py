import base64
import logging
import os
import time

import httpx
import yaml
from fastapi import FastAPI, Request

from .proxy import create_proxy_routes, filter_endpoints

app = FastAPI()

logger = logging.getLogger()
logger.name = "openapi-rest-proxy"

log_level = os.getenv("LOG_LEVEL", logging.getLevelName(logging.INFO)).upper()
logging.basicConfig(level=log_level)


def load_openapi_schema(url: str):
    """Load OpenAPI schema from URL."""
    logging.debug(f"Loading OpenAPI schema from {url}")
    response = httpx.get(url)
    response.raise_for_status()
    schema = yaml.safe_load(response.text)
    logging.debug(f"Loaded OpenAPI schema from {url}.")
    return schema


openapi_schema_url = os.getenv("OPENAPI_SCHEMA_URL")
origin_base_url = os.getenv("ORIGIN_BASE_URL")
fixed_request_headers = os.getenv("FIXED_REQUEST_HEADERS", "")
port = int(os.getenv("PORT", 8000))
host = os.getenv("HOST", "0.0.0.0")
auth_endpoint_url = os.getenv("AUTH_ENDPOINT_URL")
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
auth_scope = os.getenv("AUTH_SCOPE")

token_info = {"access_token": None, "expires_at": 0, "refresh_token": None}


def get_access_token():
    """Get OAuth2 access token for authentication."""
    if not auth_endpoint_url or not client_id or not client_secret:
        return None

    if token_info["access_token"] and token_info["expires_at"] > time.time():
        return token_info["access_token"]

    if token_info["refresh_token"]:
        response = httpx.post(
            auth_endpoint_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": token_info["refresh_token"],
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={
                "Cache-Control": "no-cache",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
    else:
        auth = f"{client_id}:{client_secret}"
        auth_base64 = base64.b64encode(auth.encode("utf-8")).decode("utf-8")
        response = httpx.post(
            auth_endpoint_url,
            data={
                "grant_type": "client_credentials",
                "scope": auth_scope,
            },
            headers={
                "Authorization": f"Basic {auth_base64}",
                "Cache-Control": "no-cache",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

    response.raise_for_status()
    token_data = response.json()
    token_info["access_token"] = token_data["access_token"]
    token_info["expires_at"] = time.time() + token_data["expires_in"]
    token_info["refresh_token"] = token_data.get("refresh_token")
    return token_info["access_token"]


if not openapi_schema_url or not origin_base_url:
    raise ValueError(
        "Environment variables OPENAPI_SCHEMA_URL and ORIGIN_BASE_URL must be set"
    )

openapi_schema = load_openapi_schema(openapi_schema_url)

# Example: ALLOW_LIST="GET:/pets|GET:/pets/{petId}"
allow_list = os.getenv("ENDPOINT_ALLOW_LIST", "").split("|")

if allow_list != [""]:
    logging.info(f"Filtering API to allow list: {allow_list}")
    openapi_schema = filter_endpoints(openapi_schema, allow_list)
else:
    logging.info("No allow list provided. Proxying all endpoints.")

create_proxy_routes(app.router, openapi_schema, origin_base_url=origin_base_url)

if fixed_request_headers:
    fixed_headers = dict(
        header.split(":") for header in fixed_request_headers.split("|")
    )
else:
    fixed_headers = {}


@app.middleware("http")
async def mutate_headers(request: Request, call_next):
    """Add fixed headers and authorization to requests."""
    mutable_headers = list(request.scope["headers"])

    for header, value in fixed_headers.items():
        logging.debug(f"Adding fixed header with key '{header}'")
        mutable_headers.append((header.lower().encode("utf-8"), value.encode("utf-8")))

    access_token = get_access_token()
    if access_token:
        mutable_headers.append(
            (b"authorization", f"Bearer {access_token}".encode("utf-8"))
        )

    request.scope["headers"] = mutable_headers

    response = await call_next(request)
    return response


@app.get("/")
def read_root():
    """Return proxy configuration information."""
    return {"origin": origin_base_url, "schema": openapi_schema_url}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=host, port=port)
