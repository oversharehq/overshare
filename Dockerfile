# Scanner API. The frontend has its own image in web/Dockerfile.
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LEAKSCAN_HOST=0.0.0.0 \
    LEAKSCAN_PORT=8000 \
    LEAKSCAN_DB_PATH=/data/scans.db

COPY pyproject.toml ./
COPY leakscan ./leakscan
RUN pip install --no-cache-dir ".[api]"

RUN useradd --create-home --uid 1001 leakscan \
    && mkdir -p /data \
    && chown -R leakscan:leakscan /data /app
USER leakscan

VOLUME ["/data"]
EXPOSE 8000

CMD ["python", "-m", "leakscan.api"]
