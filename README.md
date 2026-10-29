# Wind intelligence

A React and Python pilot for examining the wind-generation forecasts available before UK day-ahead purchasing decisions, then measuring their accuracy against retrospective actual generation. The analysis uses only Elexon **WINDFOR** and **FUELHH, fuelType=WIND**, for decisions made during January 2026.

**Delivery status:** working application and local ARM64 Docker runtime verified. Public application: **https://cmv1lh.vercel.app — deployed on Vercel Hobby and publicly verified**. The required unlisted video and final submission remain pending; this is not a completed employer submission yet.

## Business problem

A utility must buy power before it knows tomorrow's renewable output. Overestimating wind could leave a supply shortfall; underestimating it could lead to excess purchasing, all else equal. This dashboard reconstructs a defined decision-time forecast and quantifies historical error. It does not determine exact purchase volumes without customer demand, other supply commitments and market information.

The data represents the metered Great Britain wind covered by these Elexon series, not all UK renewable generation or a particular customer's portfolio.

## Stack and architecture

React 19, TypeScript, Vite 7, Tailwind CSS 4 and Recharts; Python 3.14, FastAPI, Pydantic, pandas and NumPy; pytest, Vitest/React Testing Library and retained Playwright checks; Docker Compose.

```mermaid
flowchart LR
  E[Elexon historical streams] --> R[Raw responses + provenance]
  R --> V[Validate and checksum]
  V --> S[Select publication strictly before cutoff]
  S --> A[FastAPI alignment and metrics]
  A --> U[React dashboard]
```

The frontend displays backend calculations; it does not duplicate forecast selection, interpolation, accuracy or signed-error calculations. A multi-stage Docker build compiles React, then runs only Python plus static assets. One origin serves the UI, API and health routes. No database, authentication, paid data source or runtime extraction service is required.

## Project structure

| Path | Purpose |
|---|---|
| `backend/` | Routes, response models, configuration, services, statistics, production entry point and Dockerfile |
| `pipeline/` | Elexon retrieval, normalization, duplicate/revision handling and as-of selection |
| `frontend/` | Dashboard, typed API client, charts, styling and frontend/browser tests |
| `tests/` | Data, temporal, statistical, API, real-data and production-serving tests |
| `scripts/` | Snapshot packaging, isolated Vercel preparation, HTTP verification and native shutdown check |
| `data/snapshot.tar.gz`, `snapshot.sha256` | Tracked real-data deployment bundle and integrity hash |
| `data/LICENSE.md` | Elexon dataset licence and attribution |
| `docs/api.md`, `methodology.md`, `frontend.md` | API contracts, data methodology and frontend operation |
| `docs/docker.md`, `free-deployment.md`, `deployment.md` | Container setup and current ₹0-only hosting decision |
| `deployment/vercel/`, `render.yaml` | Vercel templates and explicitly Free Render fallback |
| `docs/video-script.md`, `submission-checklist.md` | Two-part presentation and final delivery gates |
| `requirements.lock.txt` | Exact tested Python development/test environment |
| `requirements.runtime.lock.txt` | Runtime-only exact dependency subset for Docker |
| `frontend/package-lock.json` | Reproducible npm dependency graph |

Working `data/raw/` and `data/processed/` caches, virtual environments, Node modules, build output and test artifacts are ignored by Git.

## Local setup

Use Python **3.14** and a Vite-compatible Node version (20.19+ or 22.12+; Node 24 is the Docker build version). Run from the project root:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
# Restore the bundled historical sources without live API requests.
python - <<'PY'
from pathlib import Path
import hashlib, tarfile
p = Path('data/snapshot.tar.gz')
expected = Path('data/snapshot.sha256').read_text().split()[0]
assert hashlib.sha256(p.read_bytes()).hexdigest() == expected
with tarfile.open(p, 'r:gz') as archive:
    archive.extractall('.', filter='data')
PY
python -m pipeline.prepare
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173; Vite proxies `/api` to port 8000. API documentation is at http://127.0.0.1:8000/docs. Node and Python dependency installation require network access; restored data and normal analysis do not.

To reproduce extraction instead, run `python -m pipeline.fetch`, then `python -m pipeline.prepare`. Fetching makes 69 daily public API requests on a fresh cache. `--refresh` intentionally replaces cached responses. Rebuild the deployment archive with `python -m scripts.package_data` after reviewing source changes.

## Docker

With Docker running:

```sh
# Optional: copy .env.example to .env to change documented local defaults.
docker compose up --build -d --wait --wait-timeout 120
python -m scripts.verify_app --base-url http://127.0.0.1:8080
```

Open http://127.0.0.1:8080. Stop with `docker compose down`. `HTTP_PORT` changes the host port; the application honors `PORT`. Defaults bind the host service to loopback only. The image runs as uid/gid 10001, and Compose makes its root filesystem read-only, drops capabilities and supplies temporary `/tmp` storage.

The build checks the source archive hash, unpacks it and runs the original validation. The baked snapshot survives container/dyno replacement and avoids Elexon availability at startup. The verified image is **ARM64**; a hosted Docker platform may build linux/amd64 separately. Heroku paid hosting is cancelled under the ₹0 requirement. See the Docker guide for remaining image-scanning and platform checks.

## API

All analysis routes are GET. Dates are January **decision dates**, not delivery dates. Every route accepts optional `cutoff_local=HH:MM`, interpreted in Europe/London.

| Endpoint | Result |
|---|---|
| `/api/decisions` | Available decision dates, delivery dates, cutoff and coverage |
| `/api/decisions/{date}/forecasts` | Selected native hourly forecast slots and publication times |
| `/api/decisions/{date}/actuals` | Next-day half-hour WIND actuals and publications |
| `/api/decisions/{date}/comparisons` | Half-hour grid, explicit nulls/statuses and signed errors |
| `/api/decisions/{date}/metrics` | Daily retrospective MAE, RMSE, signed bias and counts |
| `/api/metrics?start_date=2026-01-01&end_date=2026-01-31` | Pooled inclusive-range metrics |

`/health/live` returns process liveness; `/health/ready` returns 200 only when validated data and any configured frontend are ready, otherwise 503. Invalid inputs receive 422; out-of-scope/unavailable dates 404; invalid source data 503. Errors use a documented `{error:{code,message}}` contract. See `docs/api.md` and generated `/openapi.json` for complete models.

## Data and forecast-selection methodology

- Decisions cover 1–31 January 2026; next-day delivery covers 2 January–1 February.
- The **09:20 London-time cutoff is an explicit scenario assumption**, based on the EPEX hourly day-ahead auction, not a universal GB rule or a confirmed client's internal deadline. Other exchanges/auctions have different times. Confirm the exchange and operational buffer before business use.
- For each delivery target, choose the latest publication **strictly earlier** than that decision's cutoff. Equality is excluded. Publication time, target time, decision time and actual publication time remain separate.
- Forecast publications are a proxy for historic availability; client receipt latency and late backfills cannot be reconstructed from current historical extracts.
- UTC is used internally. January presentation is Europe/London (GMT); conversions use timezone-aware dates.
- Exact duplicates are counted/removed; conflicting same-target/same-publication values and invalid timestamps/generation fail validation. Forecast revisions are retained. Actuals use the latest publication present in the historical snapshot.
- Only WINDFOR/FUELHH source records enter the analysis. Raw responses retain URL, retrieval time and SHA-256 provenance.

**Resolution limitation:** January WINDFOR targets are hourly points; FUELHH values are half-hour mean MW. The dashboard compares equal start times as an explicit point-versus-period proxy. The 744 structural `:30` forecast gaps remain null. Nothing is interpolated, forward-filled or treated as a zero forecast/error. These results are not full half-hour or energy-volume forecast accuracy.

## Metrics and actual results

For valid matched native targets, `error = forecast − actual`, in MW. MAE is mean absolute error; RMSE is square root of mean squared error; signed bias is mean error. Positive bias means wind was overforecast on average. Range metrics pool observations; they do not average daily metrics without weighting. Missing pairs are excluded with counts, zero actuals remain valid, and zero matched pairs produce null metrics rather than perfect scores.

| Scope at 09:20 GMT | Pairs | MAE MW | RMSE MW | Bias MW |
|---|---:|---:|---:|---:|
| All January decisions | 744 | 2,022.470430 | 2,497.407158 | +1,745.938172 |
| 1 January decision / 2 January delivery | 24 | 3,070.375000 | 3,139.279648 | +3,070.375000 |

Actuals cover all 1,488 delivery half-hours; all 744 native hourly targets have eligible forecasts. Source extraction contains 22,192 forecast records and 1,488 actuals. For 2 January 00:00 GMT, selected forecast is 18,781 MW (published 1 January 07:30 GMT), actual is 15,228 MW and signed error is +3,553 MW.

These are **retrospective historical metrics**, not information known at those procurement decisions and **not calibrated future prediction intervals**. No financial savings, exact purchase volumes or guarantee of future performance is claimed.

## Testing and verification

```sh
python -m pytest -q
cd frontend
npm test
npm run typecheck
npm run build
# Separate browser suite; requires a browser runner permitted by the host.
npm run test:e2e
```

Latest verified results: **45 Python tests + 15 frontend tests = 60 passed**. TypeScript and production build pass. Docker ARM64 startup, health, data integrity, non-root/read-only execution and graceful stop/restart were verified. HTTP verification covers all six route types, 31 dates, 1,488 rows and 744 pairs. In-app browser checks covered values, date switching, tooltips, responsive layout and errors/retry.

The separate **four Playwright CLI cases remain blocked by host Chrome-launch permissions**; they are not included in the 60 passing tests. A Vite advisory remains for the roughly 647 KB minified / 192 KB gzip chart bundle, and a Starlette/AnyIO deprecation warning remains. The final audit records security-scan and amd64 build attempts without claiming blocked checks passed.

## Deployment and delivery

**Hosting budget is strictly ₹0. The previous Heroku Basic recommendation is cancelled.** The application is deployed as one Vercel Hobby personal project for this unpaid hiring-evaluation demo. Vercel Support confirmed eligibility before deployment. `render.yaml` pins Render Free as an alternative; it sleeps after inactivity and is not one of the employer's literal named hosts.

See `docs/free-deployment.md` for official limits/terms, cold-start caveats and gated deployment steps. Build the frontend and run `python -m scripts.prepare_vercel` to create the isolated `.deploy/vercel` project. It reuses the unchanged backend, data and calculations. No paid subscription, add-on or upgrade was enabled. The deployed project uses the Hobby allowance and a free Vercel-generated domain.

- Public app URL: **https://cmv1lh.vercel.app** (Vercel Hobby; production deployment verified).
- Public anonymous GitHub URL: **https://github.com/Lakshyalamba/cmv1lh**.
- Required unlisted YouTube video: **script prepared; recording/upload pending**.
- Employer form: https://forms.cloud.microsoft/r/FTX6K2bbnU — **not submitted**.

The application is publicly deployed. Verify the app/repo/video links in an incognito session before submission. Do not submit without the video. See `docs/submission-checklist.md`.

## Attribution and licensing

Contains BMRS data © Elexon Limited copyright and database right 2026.

[Elexon BMRS open-data licence](https://www.elexon.co.uk/bsc/data/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/) applies to bundled data and derived data; see `data/LICENSE.md`. Elexon does not endorse this application. Third-party software retains its own licences, listed in `THIRD_PARTY_NOTICES.md`. No application-code licence is granted by this repository. Public visibility does not override Elexon or third-party licence terms.

## AI assistance and effort

OpenAI Codex assisted with research, architecture, Python/React implementation, tests, Docker preparation, browser/API checks and documentation/video-script drafting. Test outcomes and limitations are reported from executed checks; generated test edge cases never replace analytical source data. The candidate must review the code and be able to explain the temporal assumptions and tradeoffs independently.

The employer's total effort cap is 16 hours. The planned allocations were 2h data, 4h backend, 4h frontend, 3h infrastructure/testing and 3h final delivery. Automated session time was recorded in phase reports; candidate review, recording and deployment time must also count. No claim is made about unrecorded human effort.
