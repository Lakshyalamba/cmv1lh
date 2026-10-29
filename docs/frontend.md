# Phase 3 frontend

## Local preview

Requires Node.js 20.19+ or 22.12+ compatible with Vite 7; the tested environment used Node 26.5.0 and npm 11.17.0. Dependencies are pinned in `frontend/package-lock.json`.

Terminal 1, from the project root:

```sh
source .venv/bin/activate
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```sh
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` requests to the existing FastAPI process at 127.0.0.1:8000. No backend/CORS modifications are necessary for this local setup. The port is fixed so failure to bind is visible rather than silently opening a different port.

If npm's default cache is unwritable, use a directory you own: `npm ci --cache ./node_modules/.npm-cache`. This avoids changing global permissions. No npm install scripts required extra approval during this run; the build succeeded with the registry-installed optional native packages.

`.env.example` documents `VITE_API_BASE_URL`; leave it empty for the supported local proxy setup. A different origin would require explicit backend CORS configuration, deferred to Phase 4. Vite substitutes these values at build time; never put secrets in VITE variables.

## Architecture

- `src/main.tsx`: React StrictMode entry point.
- `src/App.tsx`: dashboard composition, date controls, loading/error/empty states, context, backend metric cards, publication detail, decision interpretation and accessible observation table.
- `src/useDashboard.ts`: overview and per-date request lifecycle. Aborts obsolete requests; old metrics are removed when date selection changes. Selecting the current date is a no-op. The selected date is checked against loaded comparison context before rendering.
- `src/api.ts`: typed fetch client, 20-second timeout, server error messages, cancellation and consistency checks across date/cutoff responses. All four daily requests must succeed before a day's analysis is displayed.
- `src/types.ts`: TypeScript interfaces corresponding to backend response models.
- `src/format.ts`: en-GB formatting with Europe/London time. No forecast selection or accuracy calculations.
- `src/Charts.tsx`: Recharts generation and signed-error visualizations.
- `src/styles.css`: Tailwind import/utilities and a restrained navy/teal/sage analytics design, responsive grids, focus styles and horizontally contained tables. No animations.
- `vite.config.ts`: React/Tailwind integration, local API proxy and Vitest configuration.
- `src/test/`: frontend tests, setup and recorded real API response fixtures. Fixtures are imported only by tests, never by production application code.
- `e2e/dashboard.spec.ts`, `playwright.config.ts`: reproducible real-backend browser verification for an unrestricted local browser runner.

The frontend does not compute MAE, RMSE, bias, signed forecast errors, forecast publication selection or data coverage. It formats and visualizes server values. Sign-based explanatory text and chart colour are presentation logic. No global state library, UI framework, date library or secondary data service was added.

## API integration

Initial load fetches `/api/decisions` and `/api/metrics` concurrently. The decision list and assumed cutoff come from the backend. The pooled January statistics appear separately as a retrospective month reference.

For the selected decision date, four requests run concurrently:

1. `/api/decisions/{date}/forecasts`: native target/publication information and source metadata.
2. `/api/decisions/{date}/actuals`: actual source and revision-policy metadata.
3. `/api/decisions/{date}/comparisons`: exact chart and observation-table values, nulls, statuses and signed errors.
4. `/api/decisions/{date}/metrics`: displayed daily MAE/RMSE/bias/counts and coverage.

Every daily request sends the effective backend cutoff as `cutoff_local`. All daily responses must agree on the selected date and cutoff. There is no frontend cutoff editor in this phase; configure the existing backend setting to change the scenario, then reload. No backend files or calculations were changed.

## Temporal and resolution presentation

- Decision date, delivery date, forecast publication and cutoff are separate fields.
- The UI labels all January presentation times as Europe/London (GMT).
- The procurement panel explains that the selected forecasts were published strictly before cutoff.
- Metric cards, actual generation and signed errors are explicitly retrospective; they are not represented as information known at decision time.
- Generation uses hourly forecast dots and a half-hour actual line. The full backend comparison grid is retained, with `connectNulls=false`; unavailable forecast half-hours are never connected or filled.
- Error bars use the backend's `forecast_mw - actual_mw`. Positive bars are amber (overforecast), negative bars teal (underforecast). Missing errors remain absent, not zero.
- The point-versus-half-hour-average limitation is visible under the main chart. Native resolution gaps are distinguished from source missingness in coverage and observation statuses.
- Insights derive direction only from signed backend bias; no demand, purchase-volume, cost-saving or calibrated uncertainty claims are made.

## Accessibility and states

Native labelled date select, named previous/next buttons, visible keyboard focus, skip link, semantic headings, text chart descriptions, textual legends and a semantic full observation table supplement the visual charts. The table scrolls within its panel on narrow screens. Tooltips use MW/GMT labels; table access provides the values without requiring pointer hover.

Loading skeletons have an accessible status. Transport/server failures have an alert, retry control and no substitute observations. Empty decision lists, no matched pairs, missing hourly forecasts/actuals and empty charts have explicit messages. Cutoff and publication timestamps remain visible with successful data. Large numbers use en-GB grouping and one decimal place; underlying server precision is preserved.

## Checks and browser evidence

```sh
npm run typecheck
npm test
npm run build
npm run test:e2e
```

`npm test` runs self-contained Vitest/React Testing Library checks. `npm run test:e2e` expects the existing data extraction and Python environment; its config can start both local servers or reuse them. It defaults to installed Google Chrome. To use Playwright Chromium instead, install it with `npx playwright install chromium`, then run `PLAYWRIGHT_CHANNEL=chromium npm run test:e2e`.

In this Codex environment, the terminal runner could not launch Chrome because of host sandbox restrictions. The four Playwright CLI cases therefore did not execute successfully; they are not reported as passing. Equivalent verification used the supported in-app browser: all 31 dates, three metrics per date, forecast-dot counts and all 1,488 table rows were compared against actual API responses. Real outage/retry, tooltip values, quick switching, previous/next boundaries and narrow/desktop layouts were also inspected. Evidence is recorded in `phase3-browser-verification.json` and `screenshots/`.

The browser's requested mobile viewport sizes were 390 and 320 pixels; the in-app browser reported effective widths of 354 and 291 pixels. Page widths stayed within those widths. Captures are original viewport screenshots because full-page capture in this browser did not reliably preserve offscreen SVG chart rendering. These limitations are disclosed rather than presenting full-page captures with missing charts.

## Remaining work and limits

- The point-versus-period comparison and assumed cutoff remain the domain limitations documented in Phase 2.
- Chart bundle is approximately 647 KB minified / 192 KB gzip. Vite reports a >500 KB chunk advisory; build succeeds. There is no code splitting in this small dashboard.
- Browser verification used the in-app engine, not a completed terminal Playwright run or a full Safari/Firefox matrix.
- Snapshot refresh/restart and backend temporal methodology are unchanged.
- Docker preparation and local ARM64 runtime verification are complete. Public deployment remains approval-gated; see `final-audit.md`.

Implementation references: [Vite guide](https://vite.dev/guide/), [Tailwind with Vite](https://tailwindcss.com/docs/installation/using-vite), [Recharts Line API](https://recharts.github.io/en-US/api/Line/). Local preview/layout guidance from the Sites skill was used; no Site was registered or published.
