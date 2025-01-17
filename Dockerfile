FROM ubuntu:24.04
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV DEBIAN_FRONTEND=noninteractive
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE ${PORT}

WORKDIR /app

COPY . .

ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

CMD ["uvicorn", "proxy.service:app", "--host", "${HOST}", "--port", "${PORT}"]
