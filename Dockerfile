FROM python:3.11-slim-trixie AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.30 /uv /bin/uv

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

FROM python:3.11-slim-trixie

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /app/.venv .venv
COPY src src

CMD ["python", "src/main.py"]
