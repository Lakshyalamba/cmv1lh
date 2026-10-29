# Docker setup and verification

**Update:** Local ARM64 container verification passed. See `docker-runtime-report.md` and `docker-runtime-verification.json` for actual image, API, health, data and stop/restart evidence. The initial blocked attempts below are historical.

## Design

One `app` service contains the backend and compiled frontend. `backend/Dockerfile` has a Node build stage and a slim Python runtime stage. A separate frontend runtime Dockerfile is unnecessary because FastAPI serves the generated static files. No Node server, reverse proxy or CORS workaround is required in production. The original two-process Vite/FastAPI development workflow still works.

Build context is the project root. `.dockerignore` excludes environments, secrets, caches, node_modules, test artifacts, documentation, source test fixtures and processed caches. Runtime images omit Node, source frontend files, pytest and HTTPX. Exact Python runtime versions are in `requirements.runtime.lock.txt`, a subset of the existing full lock. Node dependencies use `npm ci` and the existing package lock.

The snapshot archive is included deliberately. Do not exclude `data/snapshot.tar.gz` or `data/snapshot.sha256` from a clean checkout/build context. To regenerate from validated raw files:

```sh
python -m scripts.package_data
```

## Start

With Docker Desktop/Engine running, from the project root:

```sh
# Optional: customize local ports/cutoff using the documented defaults.
cp .env.example .env
docker compose up --build -d --wait --wait-timeout 120
```

Open http://127.0.0.1:8080 by default. All six API route types are under that same origin, and `/docs` provides interactive API documentation. Stop with `docker compose down`. This removes containers but not the immutable source archive.

`.env` is optional and ignored by Git/Docker. Ports in the example are defaults, not machine-specific requirements:

| Setting | Default |
|---|---|
| `BIND_ADDRESS` | `127.0.0.1` (local access only) |
| `HTTP_PORT` | `8080` (host) |
| `PORT` | `8000` (application/container; runtime reads it) |
| `WIND_DECISION_CUTOFF` | `09:20` |
| `LOG_LEVEL` | `info` |
| `NODE_IMAGE` | `node:24-bookworm-slim` build image |
| `PYTHON_IMAGE` | `python:3.14-slim-bookworm` runtime base |

If a host port is occupied, use `HTTP_PORT=8081 docker compose up --build -d --wait`. No absolute host paths, credentials, bind mounts or platform-specific sockets are embedded in Compose.

## Checks required before deployment

```sh
docker compose config --quiet
docker compose build
docker compose up -d --wait --wait-timeout 120
python -m scripts.verify_app --base-url http://127.0.0.1:8080
docker compose ps
docker compose logs --tail=100 app
docker compose exec app id
docker compose images
docker compose down
```

Confirm `id` shows uid/gid 10001, readiness is healthy, no source-validation error occurs, and the frontend uses relative `/api` paths. The runtime root filesystem is read-only under Compose, with a small writable tmpfs at `/tmp`, all Linux capabilities dropped and no-new-privileges enabled. Python bytecode writes and pip caches are disabled. A non-root USER is also present in the image.

For image vulnerability/size review, use the actual built image ID from `docker compose images` with your available scanner (`docker scout cves IMAGE` or an equivalent) and `docker image inspect IMAGE`. Do not infer a clean scan from dependency audit results or claim an image size before building. Base images use versioned moving tags so OS patches can be obtained by rebuilding; use reviewed digest-pinned image overrides for an immutable approved release.

## Health, logs and shutdown

- `/health/live`: HTTP 200 if the server is running.
- `/health/ready`: HTTP 200 only if the validated snapshot is loaded and the configured frontend build is present; otherwise 503. API-only dev startup does not require a frontend build.
- Missing/corrupt data remains a 503 for analysis endpoints; missing configured static output returns a structured 503 for `/`.
- Unknown API paths remain 404 JSON, never a successful HTML fallback.
- Platform `PORT` is validated; the main process is Python/Uvicorn, with a 20-second graceful shutdown timeout. Compose allows 25 seconds before force-killing.
- Logs go to standard output/error; exception diagnostics stay server-side and unexpected client errors get a generic structured 500 response.

## Executed versus blocked checks

`docker compose config --quiet` passed. Docker CLI 29.8.2 and Compose v5.5.1 were present. The daemon socket was absent. `docker desktop start` was unable to write Docker Desktop logs in the sandbox; `docker compose build` hit a denied buildx activity-file write, and `docker compose up` failed to connect to the daemon. These are blocked checks, not successful builds.

Linux x86-64 CPython 3.14 binary wheels for all 19 pinned runtime packages were successfully downloaded/resolved separately. This verifies package availability, not a Docker build or Linux execution. The production HTML/assets/API combination was verified as a native local process instead; image security, actual image size, read-only/non-root Linux execution and Compose startup must still be checked with a working Docker daemon.
