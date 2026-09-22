# ---------- Stage 1: builder ----------
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y \
        --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) Dependency layer: changes rarely => cached
COPY requirements.lock .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir \
       -r requirements.lock

# 2) Source layer: changes every commit, cheap
COPY pyproject.toml README.md ./
COPY src/ src/
RUN /opt/venv/bin/pip install --no-cache-dir --no-deps .

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim AS runtime
RUN useradd --create-home --uid 10001 appuser
RUN apt-get update && apt-get install -y \
    --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
# 3) Model layer: a retrain won't invalidate the source cache
COPY models/fraud_model.joblib models/fraud_model.joblib

ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s \
    --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/v1/ready || exit 1
CMD ["uvicorn", "fraud_service.api.app:create_app", \
     "--factory", "--host", "0.0.0.0", "--port", "8000"]
