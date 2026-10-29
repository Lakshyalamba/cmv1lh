# Docker runtime verification — passed locally on ARM64

The user built the production image in their Mac Terminal: Docker Compose reported a successful build in 161.9 seconds and a healthy container. This session independently inspected and exercised the actual image/container; this is no longer a native-process-only verification.

| Check | Actual result |
|---|---|
| Build | Passed in user's Terminal; resulting image independently inspected |
| Container | `gridbricks-assignment-app-1`, healthy |
| Frontend | Container-served HTML and assets loaded; charts/date switching/tooltip verified in the in-app browser |
| Six API route types | Passed across all 31 January decision dates |
| Actual observation grid | 1,488 rows; 744 matched pairs |
| Data inside container | Original loader/checksums passed: 22,192 WINDFOR and 1,488 FUELHH records; 138 raw/provenance JSON files |
| Health | `/health/live` and `/health/ready` returned 200; internal readiness request returned 200; Docker health status healthy |
| Shutdown | `docker compose stop --timeout 25 app` exited cleanly; container exit code 0; application shutdown-complete log present |
| Restart | `docker compose up -d --wait --wait-timeout 120` returned healthy; HTTP verifier passed again afterwards |
| Logs | No ERROR, Traceback or Exception lines found in application container logs |
| Runtime identity | uid/gid 10001:10001 |
| Compose isolation | Read-only root filesystem and ALL Linux capabilities dropped |
| Image | Linux ARM64; 366,646,814 bytes (about 350 MiB), as reported by Docker |
| Backend tests | 45 passed, one existing dependency deprecation warning |
| Frontend unit/component tests | 15 passed |
| TypeScript | Passed |
| Production build | Passed; existing 647 KB JS chunk advisory remains |
| Playwright CLI | Four cases could not launch Chrome in the host sandbox; these are not reported as passing |

The browser reloaded from the actual container origin, selected January 31 and January 1, and verified 24 native forecast dots. The January 1 tooltip showed forecast 18,781 MW and actual 15,228 MW at 00:00 GMT. No runtime console errors were observed. All-date API verification also passed after restart.

Pooled container API metrics remain MAE 2,022.470430 MW, RMSE 2,497.407158 MW and signed bias +1,745.938172 MW over 744 pairs.

## Fixes and documentation

No Docker-specific application fix was needed. No calculation, frontend or configuration functionality changed. This report/evidence and status updates supersede the earlier Phase 4 notes that Docker execution was blocked. Application/data source files remain unchanged.

## Remaining limits

- Local Docker verification is complete for ARM64. The Heroku-targeted linux/amd64 image has not yet been built/run; do that before a Heroku release.
- A container CVE scan is not claimed. Earlier npm audit results are not a substitute for an image scan.
- Standalone Playwright remains blocked by Chrome launch permissions. Run `npm run test:e2e` in your own Terminal for that remaining browser automation check; existing Python/frontend tests do pass.
- Nothing has been deployed or published. Phase 5 has not started.

The user-started container is left running at http://127.0.0.1:8080 for review. Stop it with `docker compose down` from the project root when finished.

Commands executed here included `docker compose ps`, `docker compose exec -T app ...`, `python -m scripts.verify_app`, health HTTP requests, `docker image inspect`, `docker inspect`, `docker compose logs`, Compose stop/restart, pytest, npm test/typecheck/build and the blocked Playwright attempt. Structured evidence is in `docker-runtime-verification.json`.

Stopped after verification, awaiting approval.
