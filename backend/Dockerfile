# Build from the repository root: docker build -f backend/Dockerfile .
ARG NODE_IMAGE=node:24-bookworm-slim
ARG PYTHON_IMAGE=python:3.14-slim-bookworm
FROM ${NODE_IMAGE} AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    WIND_DATA_ROOT=/app WIND_STATIC_DIR=/app/static PORT=8000
WORKDIR /app
COPY requirements.runtime.lock.txt ./
RUN pip install --no-compile --only-binary=:all: -r requirements.runtime.lock.txt \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-create-home app
COPY backend/ ./backend/
COPY pipeline/ ./pipeline/
# Baked immutable historical snapshot; no extraction during startup.
COPY data/snapshot.tar.gz data/snapshot.sha256 ./data/
RUN sha256sum -c data/snapshot.sha256 \
    && tar -xzf data/snapshot.tar.gz -C /app \
    && rm data/snapshot.tar.gz
COPY --from=frontend-build /build/frontend/dist/ ./static/
# Fail the build rather than ship an incomplete, corrupt or unusable data bundle.
RUN python -c "from pipeline.prepare import load_sources; load_sources()"
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/health/ready',timeout=4)"
CMD ["python", "-m", "backend.run"]
