> Historical preparation report. For current delivery status and the live application URL, see the repository README. Statements about pending deployment describe the time of this report.

# Final engineering and delivery audit

Reviewed 29 October 2026 against the original internship challenge, re-read completely before this phase. This report describes preparation, not a completed employer submission.

## Employer requirements

| Requirement | Evidence/status |
|---|---|
| React frontend + Python backend | Implemented; TypeScript/Vite/Tailwind/Recharts and FastAPI |
| Only Elexon FUELHH WIND + WINDFOR | Source archive, original extraction pipeline and provenance retained |
| January 2026 purchase decisions | All 31 decision dates verified; delivery 2 January–1 February |
| Forecasts available at procurement | Latest publication strictly before assumed 09:20 London cutoff; equality excluded |
| Quantitative accuracy | Backend MAE/RMSE/signed bias with units, counts and explicit missingness |
| Docker | Actual local ARM64 image/runtime, data, health, stop/restart and security settings verified |
| Vercel or Heroku deployment | Not deployed; comparison and recommendation prepared; architecture approval required |
| Anonymous/random public GitHub repo | Local sanitized Git package prepared with short random name; not published |
| README structure/startup/app link | Complete documentation; actual public app URL pending deployment |
| Explicit AI disclosure | Present in README, including research/code/tests/docs assistance |
| Unlisted two-part YouTube video <=10 min | Detailed timed script prepared; recording/upload pending |
| Incognito URL checks and form | Checklist prepared; no URLs invented and no form submitted |
| <=16-hour total effort | Candidate must include actual review/recording/deployment time; no unrecorded human-effort claim |

## Regression and data verification

- **45 Python tests passed**, including all original Phase 1/2 cases and production tests.
- **15 frontend tests passed** after the attribution-only footer update.
- TypeScript and production build passed. Latest JS bundle is about 647 KB minified / 192 KB gzip; Vite's chunk advisory remains.
- The complete six-route HTTP verification passed against the actual container: 31 dates, 1,488 grid rows and 744 matched native targets, with ready health.
- Snapshot checksums and original normalization preserve 22,192 forecast records and 1,488 actuals. The tracked archive contains 138 raw/provenance files.
- A clean source-copy restored the tracked archive and passed the same 45 Python tests using the already-installed locked test environment. This verifies source/data completeness; it is not a fresh Python dependency installation claim.
- Docker runtime verification remains ARM64. Container uid/gid 10001, read-only root and dropped capabilities were inspected; stop returned exit 0, restart became healthy, and no runtime error lines were found in its logs.
- Separate Playwright CLI cases remain unverified because Chrome cannot launch in this host sandbox. They are not included in the 60 passing tests. Supported in-app browser verification is recorded separately.
- The running local image predates the attribution-only footer change; rebuild the final source before public deployment. Data/calculation functionality was unchanged.

## Security, privacy and packaging

The public candidate excludes `.venv`, node_modules, generated frontend builds, local raw/processed caches, test-results, logs, historical phase reports and local Git history. Exact runtime/dev lockfiles and the real-data snapshot are included. Ignore rules cover root/frontend .env files while retaining environment examples.

A text-pattern review of candidate source/docs and the JSON members of the compressed data archive found no candidate-owner username, absolute personal filesystem paths, Mac host identity, private-key blocks or common token/key patterns. This is an audit of the prepared files, not a guarantee against every possible secret format. Upstream copyright names in required third-party notices are intentionally preserved; they are not candidate-owner identity. Generated Git metadata is local-only; no commit, author identity or remote was inserted.

Two historical reports contained machine-specific project paths; those were replaced with `<project-root>` in the working copy and omitted from the curated public package. The dashboard now includes Elexon's required exact attribution and licence link. `data/LICENSE.md` records data terms; `THIRD_PARTY_NOTICES.md` records licences for the locked runtime distributions. No application-code licence was assigned automatically.

npm audit reported **zero known vulnerabilities** in the current dependency graph. Docker Scout is installed, but `docker scout cves local://gridbricks-assignment-app` could not initialize its cache under `~/Library/Caches/fanal` due to sandbox permissions. **No clean image-CVE result is claimed.** Run that command in the operator's Mac Terminal and review findings before publication.

The Heroku-targeted `docker buildx build --platform linux/amd64 ... --load` attempt failed writing `~/.docker/buildx/activity` in this sandbox. No workaround or registry push was used. The known-working ARM64 image is not falsely described as an amd64 build. Run the amd64 command on the Mac before a Heroku release, then verify the resulting local container on an unused host port.

## Changes in this phase

Application behavior change: **none**. The footer gained mandatory source attribution only. Documentation was completed/reorganized, historical owner paths sanitized, third-party/data notices added, the video script/checklist drafted, and a curated random-name local Git package prepared. Backend selection, metrics, source data and API contracts were preserved.

The original pipeline scripts still retrieve/validate real sources. No recording, upload, deployment, public repository or submission was performed.

## Hosting decision — superseded by strict ₹0 requirement

The previous paid Heroku Basic recommendation is cancelled. The prepared candidate is now one Vercel Hobby personal project for the user's confirmed unpaid personal evaluation demo, with an explicitly Free Render fallback. See `free-deployment.md` for current policy assessment, size checks, cold-start limitations and approval-gated steps. No subscription, payment method, paid add-on or upgrade is authorized.

## Ready for review; remaining gates

1. Approve an eligible free platform only; no recurring cost is permitted. Complete its provider-specific build/scan checks before a release.
2. Review the anonymous repository name, staged source and intended commit identity, then separately authorize public GitHub publication.
3. Deploy only after authorization; verify public readiness and all-date behavior, and insert the actual URL into README.
4. Rehearse/record the prepared two-part script, then separately authorize an **unlisted** upload. No recording/upload was done here.
5. Verify app, repo and video URLs in incognito; obtain explicit approval before submitting the Microsoft form.

The video has approximately 500 customer words and 550 technical words, with screen actions and a target duration under 10 minutes. Actual timing must be rehearsed. Approximate additional automated Phase 5 preparation effort was about 15 minutes, excluding candidate review, recording and deployment; all human time must count toward the employer's cap.
