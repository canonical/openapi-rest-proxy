import logging
from httpx import Request, AsyncClient
from fastapi.routing import APIRouter
from fastapi import Request, Response


def create_proxy_handler(method: str, path: str, origin_base_url: str):
    async def proxy_handler(request: Request):
        return await proxy(
            request, method=method, path=path, origin_base_url=origin_base_url
        )

    return proxy_handler


def filter_endpoints(schema: dict, allow_list: list):
    logging.debug("Filtering endpoints...")
    logging.debug(f"Allow list: {allow_list}")
    filtered_paths = {}
    for path, methods in schema.get("paths", {}).items():
        for method in methods.keys():
            method_path_combo = f"{method.upper()}:{path}"
            formatted_method_path_combo = f"{method.upper()} {path}"

            logging.debug(f"Checking {method_path_combo}")
            if method_path_combo in allow_list:
                logging.info(f"Allowing {formatted_method_path_combo}")
                if path not in filtered_paths:
                    filtered_paths[path] = {}
                filtered_paths[path][method] = methods[method]
            else:
                logging.debug(f"Not allowing {formatted_method_path_combo}")

    if not filtered_paths or not filtered_paths.keys():
        raise ValueError("No endpoints matched the allow list.")

    filtered_schema = schema.copy()
    filtered_schema["paths"] = filtered_paths
    return filtered_schema


def create_proxy_routes(router: APIRouter, schema: dict, origin_base_url: str):
    logging.debug("Creating proxy routes...")

    for path, methods in schema.get("paths", {}).items():
        for method, _operation in methods.items():
            method_name = method.upper()

            router.add_api_route(
                path=path,
                endpoint=create_proxy_handler(method_name, path, origin_base_url),
                methods=[method_name],
            )
            logging.info(f"Registered route {method_name} {path}")

    logging.debug("Proxy routes created.")


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

    async with AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=body,
        )

        return Response(
            content=response.text,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
