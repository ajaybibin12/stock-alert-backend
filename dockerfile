# Dockerfile
FROM python:3.13.5-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies you may need (postgres client libs, build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev netcat && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy and install python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Production startup (web) - fly apps will override CMD for worker/beat
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
