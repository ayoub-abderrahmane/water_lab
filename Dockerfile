FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen

COPY src ./src
COPY front ./front
COPY models ./models

ENV PATH="/app/.venv/bin:$PATH"