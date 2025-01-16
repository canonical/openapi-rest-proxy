import httpx
import yaml
import logging
import argparse
import os

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute

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


def filter_endpoints(schema: dict, allow_list: list):
    logging.debug("Filtering endpoints...")
    logging.debug(f"Allow list: {allow_list}")
    filtered_paths = {}
    for path, methods in schema.get("paths", {}).items():
        for method in methods.keys():
            method_path_combo = f"{method.upper()}:{path}"
            logging.debug(f"Checking {method_path_combo}")
            if method_path_combo in allow_list:
                logging.info(f"Allowing path: {method.upper()} {path}")
                if path not in filtered_paths:
                    filtered_paths[path] = {}
                filtered_paths[path][method] = methods[method]

    if not filtered_paths or not filtered_paths.keys():
        raise ValueError("No endpoints matched the allow list.")

    filtered_schema = schema.copy()
    filtered_schema["paths"] = filtered_paths
    return filtered_schema


async def proxy(request: Request, method: str, path: str, origin_base_url: str):
    logging.info(f"Proxying {method.upper()} {path}")

    url = f"{origin_base_url}{path}"
    params = dict(request.query_params)

    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ["host", "content-length"]
    }
    body = await request.body()

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=body,
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )


def create_proxy_handler(method: str, path: str, origin_base_url: str):
    async def proxy_handler(request: Request):
        return await proxy(
            request, method=method, path=path, origin_base_url=origin_base_url
        )

    return proxy_handler


def create_proxy_routes(schema: dict, origin_base_url: str):
    logging.debug("Creating proxy routes...")

    for path, methods in schema.get("paths", {}).items():
        for method, _operation in methods.items():
            route_path = path.lstrip("/")  # Drop leading slash

            logging.info(f"Registering route: {method.upper()} /{route_path}")
            app.router.add_api_route(
                path=f"/{route_path}",
                endpoint=create_proxy_handler(method.upper(), path, origin_base_url),
                methods=[method.upper()],
            )
    logging.debug("Proxy routes created.")


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

create_proxy_routes(openapi_schema, origin_base_url=origin_base_url)


@app.get("/")
def read_root():
    return {"message": "Welcome to the proxy service!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=host, port=port)
