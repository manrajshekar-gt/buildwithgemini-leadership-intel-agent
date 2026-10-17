# Production Dockerfile for Leadership Intelligence Platform
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app:/app/frontend" \
    PORT=8080

# Install production dependencies
COPY frontend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code & assets
COPY ./app ./app
COPY ./frontend ./frontend
COPY ./scripts ./scripts
COPY ./seed_all_indexed_companies.py ./seed_all_indexed_companies.py
COPY ./data /app/data

EXPOSE 8080

CMD ["uvicorn", "frontend.main:app", "--host", "0.0.0.0", "--port", "8080"]
