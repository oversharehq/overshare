# Scanner API. The frontend has its own image in web/Dockerfile.
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OVERSHARE_HOST=0.0.0.0 \
    OVERSHARE_PORT=8000 \
    OVERSHARE_DB_PATH=/data/scans.db

COPY pyproject.toml ./
COPY overshare ./overshare
RUN pip install --no-cache-dir ".[api]"

RUN useradd --create-home --uid 1001 overshare \
    && mkdir -p /data \
    && chown -R overshare:overshare /data /app
USER overshare

VOLUME ["/data"]
EXPOSE 8000

CMD ["python", "-m", "overshare.api"]
