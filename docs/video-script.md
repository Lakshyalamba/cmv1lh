# Unlisted video script and screen-by-screen recording plan

Target **9 minutes 10 seconds**, with a hard stop at 10 minutes. Part 1 runs 0:00–4:25 (under 5 minutes); Part 2 runs 4:25–9:10 (under 5 minutes). Rehearse at a natural 125–140 words/minute; screen transitions consume the remaining time. Do not speed-read to fill a timing slot. If a rehearsal runs long, shorten narration rather than exceed either limit.

**Before the final recording:** use the approved public deployment after it passes verification. Until then, rehearse at localhost and describe it as a local pilot. Do not say it is deployed while no public URL exists. The spoken lines below do not claim a deployment, scan or amd64 result that has not occurred. Update the final verification sentence only after additional checks actually pass.

## Part 1 — customer presentation

### 0:00–0:40 — browser: dashboard overview, 1 January selected

**Show:** title, decision-date selector, cutoff and delivery context. Keep the cursor still while explaining.

**Say:**

“Utilities buy electricity ahead of delivery, but tomorrow's wind output is uncertain. If we assume more wind than actually arrives, other things equal, we can be left short of supply. If we assume too little, we may buy more than we need.

This pilot helps an analyst see the forecast available at a defined purchasing decision, then evaluate it against what happened afterwards. It uses two Elexon datasets for metered wind in Great Britain. It is an evidence tool, rather than an automatic purchasing recommendation.”

### 0:40–1:25 — browser: decision context and publication

**Show:** decision 1 January 2026; delivery 2 January; 09:20 cutoff; selected publication 1 January 07:30 GMT; 24/24 forecast targets and 48/48 actuals.

**Say:**

“I've selected the first of January. The electricity delivery day is the second of January. The assumed decision cutoff is nine twenty London time. This models an hourly day-ahead auction scenario; the actual client's exchange and internal deadline would need confirmation.

For each delivery target, the application selects the latest forecast published strictly before that cutoff. On this date, the selected publication is seven thirty that morning. Later revisions are not used. The actual generation and accuracy statistics are retrospective: the purchasing team did not know them at that time.”

### 1:25–2:20 — browser: generation chart, tooltip, resolution caveat

**Show:** hover/click the 00:00 target; tooltip forecast 18,781 MW, actual 15,228 MW. Briefly point to the resolution note and the two legend entries.

**Say:**

“The green dots show the wind forecast available before procurement. The other line shows actual generation after delivery. At midnight, the forecast was eighteen thousand seven hundred and eighty-one megawatts, while actual generation was fifteen thousand two hundred and twenty-eight. That is an overforecast of three thousand five hundred and fifty-three megawatts at this matched timestamp.

There is an important limitation. The forecast has hourly target points, while the actuals are half-hour averages. We compare matching start times as a transparent proxy. We do not invent a forecast for the intervening half-hours, and the interface keeps that distinction visible.”

### 2:20–3:20 — browser: metric cards and signed error chart

**Show:** daily MAE, RMSE, bias and count, then error chart. Avoid confusing these daily values with the separate January reference.

**Say:**

“For this decision, the mean absolute error is three thousand and seventy point four megawatts. This describes the average size of the miss, without its direction.

Root mean squared error is three thousand one hundred and thirty-nine point three megawatts. It puts more weight on large errors. Signed bias is plus three thousand and seventy point four megawatts, so wind was overforecast on average across the twenty-four matched targets.

The error chart keeps the direction explicit: forecast minus actual. Amber positive bars mean overforecast; teal negative bars mean underforecast. Blank half-hours are missing forecast comparisons, not zero errors.”

### 3:20–4:25 — browser: January 31, insights, monthly reference

**Show:** select 31 January and point to 1 February delivery; return to 1 January if convenient; show insights and pooled January reference.

**Say:**

“The selector covers decisions throughout January, including the thirty-first, whose delivery day is the first of February.

Across all January decisions, the pooled mean absolute error is two thousand and twenty-two point five megawatts, with signed bias of plus one thousand seven hundred and forty-five point nine, across seven hundred and forty-four pairs. These are monthly historical results, separate from the selected day's metrics.

The practical value is a consistent view of what was forecast and how large the subsequent misses were. Historical error helps frame uncertainty, but it is not a calibrated prediction interval for tomorrow. Wind alone also cannot tell us the exact amount to buy: we still need customer demand, other supply commitments and market conditions.”

## Part 2 — technical review

### 4:25–5:00 — editor: README architecture and project tree

**Show:** `README.md` architecture diagram; folders `frontend`, `backend`, `pipeline`, `data`, `tests`, `scripts`.

**Say:**

“React and TypeScript provide the dashboard, FastAPI provides typed endpoints, and pandas and NumPy handle validation and statistics.

The production container builds the frontend once and serves its static files through the same FastAPI origin. That avoids a second application server and cross-origin configuration. There is no database because the challenge is a fixed historical analysis.”

### 5:00–5:55 — editor: extraction and validation

**Show:** `pipeline/fetch.py`, then `load_sources` and `normalize` in `pipeline/prepare.py`; source archive metadata, not thousands of raw rows.

**Say:**

“The retrieval script requests the Elexon streams in daily windows, filters actuals to WIND and preserves target and publication timestamps. Each response retains its URL, retrieval time and checksum.

Normalization requires timezone-aware timestamps and valid generation values. Exact duplicates are counted and removed; conflicting records fail visibly. Revisions remain separate so we can reconstruct the information available before a decision.

The tracked deployment archive contains these validated real responses and provenance. It is checked and expanded during the image build, so a clean checkout does not depend on ignored local caches or on an external API at startup.”

### 5:55–6:40 — editor: cutoff and alignment

**Show:** `cutoff` and `align` in `pipeline/prepare.py`, especially `publishTime < cutoff(...)`; point to next-day grid and null-preserving joins.

**Say:**

“The key temporal condition is publication time strictly earlier than decision cutoff. We then choose the most recent eligible publication for each target on the following delivery day. Using an unrestricted latest forecast here would leak future publications.

UTC is used internally, with Europe/London conversion for decision boundaries and display. Actuals are allowed to be published later because they are the retrospective scoring reference, never an input to selecting the forecast. ”

### 6:40–7:25 — editor/API docs: statistics and route design

**Show:** `backend/analytics.py`, `models.py`, `routes.py`; `/docs` if convenient.

**Say:**

“The backend computes errors as forecast minus actual, then MAE, RMSE and signed bias over valid matched pairs. Counts and coverage accompany those metrics. Missing pairs are excluded; no matches returns null metrics. Zero actual generation is valid, and we avoid unstable percentage errors.

There are six analysis route types: decision dates, forecasts, actuals, comparisons, daily metrics and pooled metrics. Pydantic models describe their responses. Routes delegate to services and the original pipeline instead of embedding selection or statistical logic in HTTP handlers.”

### 7:25–8:05 — editor: frontend data flow and charts

**Show:** `frontend/src/api.ts`, `useDashboard.ts`, then `Charts.tsx` with `connectNulls={false}` and `error_mw`.

**Say:**

“The frontend fetches typed responses and displays server values. It does not recalculate accuracy. The request hook cancels obsolete requests, clears stale metrics, and handles loading, empty and error states with retry.

The generation chart preserves the full comparison grid. Forecast dots are not connected across null half-hours. The error bars use the backend's signed errors directly. A semantic observation table provides exact values without requiring pointer interaction with a chart.”

### 8:05–9:10 — editor/terminal: Docker, tests, tradeoffs, disclosure

**Show:** `backend/Dockerfile`, `docker-compose.yml`, verified test output/report, then README limitations and AI disclosure. Use actual outputs; do not run an unverified deployment command on video.

**Say:**

“The multi-stage Docker build keeps Node and development tools out of the runtime image. The application runs as a non-root user. Local Compose uses a read-only root filesystem, dropped capabilities and readiness checks. The ARM64 container has been verified for data access, all decision dates, health checks and graceful stop and restart.

The project has sixty passing Python and frontend tests, plus TypeScript and production-build checks. These include cutoff boundaries, revisions, missing data, metric edge cases, API errors and UI states. Chrome-launch restrictions block the separate browser suite; those cases are excluded from the passing count. In-app browser checks verified the dashboard against real responses.

The main tradeoffs are deliberate: a small historical snapshot instead of extra infrastructure, an explicit cutoff scenario, and honest point-versus-period comparisons. Codex assisted with research, implementation, verification and documentation, as disclosed in the README. The methodology and remaining deployment checks are documented so the work is easy to review.”

## Recording checklist

- [ ] Rehearse both parts; each must remain under 5 minutes and total under 10. Target 9:10, leaving 50 seconds of margin.
- [ ] Use the final approved public app after verification, or clearly identify a rehearsal as local. Do not show a pending URL as deployed.
- [ ] Record only the browser content and editor workspace. Hide account menus, notifications, bookmarks, personal tabs, usernames, absolute personal paths and terminal prompt identity.
- [ ] Open the selected day's metrics/comparison API response beforehand for cross-checking. Do not use fabricated demo data.
- [ ] Stage browser at 1 January, ready to show midnight tooltip, metric cards, error chart and 31 January/1 February delivery.
- [ ] Stage editor tabs: README; `fetch.py`; `prepare.py`; `analytics.py`; `models.py`; `routes.py`; `api.ts`; `useDashboard.ts`; `Charts.tsx`; Dockerfile; Compose; test report.
- [ ] Use a readable editor font and browser zoom; keep technical identifiers visible only in the technical section.
- [ ] Use real verified logs/test output. Mention ARM64 scope and blocked browser/scan/amd64 checks accurately; update wording only after those checks actually pass.
- [ ] Speak in your own words and be able to explain each line shown. Do not claim you personally authored every line without AI assistance.
- [ ] Check microphone levels, cursor visibility, subtitles and playback. Avoid background music and unnecessary transitions.
- [ ] Review the recording for numerical accuracy, timing and personal information before upload.
- [ ] Upload only with explicit approval, set visibility to **Unlisted**, and test the actual watch URL in an incognito session.
