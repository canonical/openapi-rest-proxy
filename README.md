# OpenAPI REST Proxy

This project is an OpenAPI REST Proxy that allows you to easily create a RESTful API based on an OpenAPI specification.

## Running instructions

Make sure you have [uv](https://docs.astral.sh/uv/) installed.

1. Clone the repository:

   ```sh
   git clone https://github.com/yourusername/openapi-rest-proxy.git
   cd openapi-rest-proxy
   ```

2. Start the server:

   ```sh
   ENDPOINT_ALLOW_LIST='GET:/api/v2/certified-configurations' \
   OPENAPI_SCHEMA_URL='https://certification.canonical.com/api/v2/openapi' \
   ORIGIN_BASE_URL='https://certification.canonical.com' \
   HOST='0.0.0.0' \
   PORT=8000 \
   uv run uvicorn proxy.service:app --reload
   ```

The server will be running at `http://localhost:8000` by default.

## Configuration

The following environment variables can be set to configure the server:

- `ENDPOINT_ALLOW_LIST`: A comma-separated list of allowed endpoints (e.g., `GET:/api/v2/certified-configurations`).
- `OPENAPI_SCHEMA_URL`: The URL of the OpenAPI schema to use (e.g., `https://certification.canonical.com/api/v2/openapi`).
- `ORIGIN_BASE_URL`: The base URL of the origin server (e.g., `https://certification.canonical.com`).
- `PORT`: The port on which the server will run (default is `8000`).
- `HOST`: The host on which the server will run (default is `0.0.0.0`).

## Running tests

```sh
uv run pytest
```

## License

This project is licensed under the Affero GPL 3.0 License.
