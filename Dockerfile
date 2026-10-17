# Copyright 2026 Google LLC
# Production Dockerfile for Leadership Intelligence Platform

FROM python:3.12-slim

RUN pip install --no-cache-dir uv==0.8.13

WORKDIR /code

COPY ./pyproject.toml ./README.md ./uv.lock* ./

COPY ./app ./app
COPY ./frontend ./frontend
COPY ./data ./data

RUN uv sync --frozen

ARG AGENT_VERSION=0.1.0
ENV AGENT_VERSION=${AGENT_VERSION} \
    PYTHONPATH="/code:/code/frontend" \
    PYTHONUNBUFFERED=1 \
    PORT=8080

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "frontend.main:app", "--host", "0.0.0.0", "--port", "8080"]
