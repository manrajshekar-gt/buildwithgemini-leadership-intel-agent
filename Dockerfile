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

# Copy application source code and pre-indexed data
COPY ./app ./app
COPY ./frontend ./frontend
COPY ./data ./data

EXPOSE 8080

CMD ["uvicorn", "frontend.main:app", "--host", "0.0.0.0", "--port", "8080"]
