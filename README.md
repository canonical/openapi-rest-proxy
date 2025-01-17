# OpenAPI REST Proxy ![Unit tests](https://github.com/canonical/openapi-rest-proxy/actions/workflows/unit_test.yml/badge.svg) ![Integration tests](https://github.com/canonical/openapi-rest-proxy/actions/workflows/integration_test.yml/badge.svg)

This project is an OpenAPI REST Proxy that allows you to easily create a RESTful API based on an OpenAPI specification, filtering through a selection of allowed endpoints.

The proxy service passes request headers to the origin it is configured to proxy, and similarly passes through response headers from the origin (right now without particular smarts).

## Running instructions

Make sure you have [uv](https://docs.astral.sh/uv/) installed.

1. Clone the repository:

   ```sh
   git clone https://github.com/canonical/openapi-rest-proxy.git
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

- `ENDPOINT_ALLOW_LIST`: A `|`-separated list of allowed endpoints in the format `METHOD:PATH` (e.g., `GET:/api/v2/certified-configurations`). `|` is used as a delimiter since it is not itself a valid character in a path.
- `OPENAPI_SCHEMA_URL`: The URL of the OpenAPI schema to use (e.g., `https://certification.canonical.com/api/v2/openapi`).
- `ORIGIN_BASE_URL`: The base URL of the origin server (e.g., `https://certification.canonical.com`).
- `PORT`: The port on which the server will run (default is `8000`).
- `HOST`: The host on which the server will run (default is `0.0.0.0`).
- `FIXED_REQUEST_HEADERS`: A `|`-separated list of fixed request headers in the format `HEADER:VALUE` (e.g., `Authorization:Bearer token|X-Custom-Header:Value`) which are included in all requests to the origin.
- `AUTH_ENDPOINT_URL`: The URL of the OAuth2 token endpoint (e.g., `https://auth.example.com/o/token/`).
- `CLIENT_ID`: The client ID for OAuth2 authentication.
- `CLIENT_SECRET`: The client secret for OAuth2 authentication.
- `AUTH_SCOPE`: The scope for OAuth2 authentication (optional).

## Running unit tests

```sh
uv run pytest tests/unit
```

## Running integration tests

To run the integration tests, you need to have a server up serving the test fixtures (example toy OpenAPI schema and a toy API response). Easiest accomplished for local development with the help of [docker-compose](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository). In the root of the project, issue the following:

```sh
docker-compose up schema -d
```

Once you have the test fixture server running, run integration tests from the root of the project:

```sh
uv run pytest tests/integration
```

## License

This project is licensed under the Affero GPL 3.0 License.
