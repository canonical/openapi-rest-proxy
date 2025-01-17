FROM ubuntu:24.04
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV DEBIAN_FRONTEND=noninteractive
ENV HOST=0.0.0.0
ENV PORT=8000
ENV ENDPOINT_ALLOW_LIST=""
ENV OPENAPI_SCHEMA_URL=""
ENV ORIGIN_BASE_URL=""

EXPOSE ${PORT}

RUN apt-get update && \
    apt-get install -y python3.12 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

CMD uv run uvicorn proxy.app:app --host $HOST --port $PORT
