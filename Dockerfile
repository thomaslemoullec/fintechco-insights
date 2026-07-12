# Container image for the Macro Insights dashboard (FastAPI + static UI, one process).
# Deployed to Cloud Run behind IAP (identity-gated, no public/unauthenticated access).
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App code + committed synthetic fixtures (no real/personal data).
COPY services ./services
COPY scripts ./scripts

EXPOSE 8080
# Cloud Run provides $PORT (defaults to 8080). Shell form so it expands.
CMD ["sh", "-c", "exec uvicorn app.main:app --app-dir services/insights --host 0.0.0.0 --port ${PORT:-8080}"]
