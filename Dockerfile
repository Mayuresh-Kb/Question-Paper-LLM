FROM node:22.15-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY Question-generation-project-integrated-frontend/package.json Question-generation-project-integrated-frontend/package-lock.json ./
RUN npm ci
COPY Question-generation-project-integrated-frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS application
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STORAGE_DIR=/data \
    FRONTEND_DIST=/app/static \
    CORS_ORIGINS="" \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system questionpaper \
    && useradd --system --gid questionpaper --home-dir /app questionpaper

WORKDIR /app
COPY Question-Paper-Generation-main/requirements-lock.txt ./requirements-lock.txt
RUN python -m pip install --no-cache-dir -r requirements-lock.txt
COPY Question-Paper-Generation-main/ ./
COPY --from=frontend /build/frontend/dist/ /app/static/

RUN mkdir -p /data && chown -R questionpaper:questionpaper /app /data
USER questionpaper

EXPOSE 8000
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"

CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
