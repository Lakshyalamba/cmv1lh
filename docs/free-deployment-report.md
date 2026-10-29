> Historical preparation report. For current delivery status and the live application URL, see the repository README. Statements about pending deployment describe the time of this report.

# ₹0 deployment preparation — complete, not deployed

## Decision

The paid Heroku Basic recommendation is cancelled. Preferred configuration: **one Vercel Hobby personal project**, for the user's confirmed unpaid personal evaluation demo. This is a reasonable eligibility interpretation, not an explicit hiring-assignment exception or provider confirmation. If current terms/account checks reject Hobby use, stop and use the separately approved Render Free option; never upgrade to paid hosting.

Render Free is pinned in a fallback Blueprint. It sleeps after 15 idle minutes, with documented wake-up around one minute; no always-on promise. Render is not one of the employer's named Vercel/Heroku hosts, so obtain employer acceptance before submitting a Render-only URL.

## Exact changes

Created `deployment/vercel/app.py`, `vercel.json`, `.vercelignore`, and `scripts/prepare_vercel.py`. The script validates the immutable data archive and creates `.deploy/vercel/` with the original backend/pipeline, exact runtime-only requirements, Python 3.14 selector, expanded raw data and compiled React assets. One origin serves the frontend and the same six API endpoints. No backend, forecast, statistics, source data or Docker runtime functionality was changed.

Created `render.yaml` with `runtime: docker`, **`plan: free`**, the existing Dockerfile, readiness route, and `autoDeployTrigger: "off"`; no paid disks/databases/services are declared. Git/Docker ignore rules now exclude generated `.deploy`/`.vercel` artifacts. README/current deployment comparison/guides cancel the previous paid recommendation and link the ₹0-only plan. The historical Heroku manifest is labelled cancelled and omitted from the updated public source candidate.

## Verification

- 45 Python tests passed; 15 frontend tests passed.
- TypeScript and production build passed.
- Both Vercel JSON and Render YAML validated against official provider schemas.
- Generated Vercel entry point started under local ASGI using only its bundled source/data/static paths.
- All six route types and all 31 dates passed HTTP checks against the isolated adapter: 1,488 grid rows, 744 matched pairs, readiness healthy.
- All manifest hashes remained unchanged after requests; original snapshot SHA-256 is preserved.
- Local browser loaded the adapter-served React app, changed January dates and displayed the actual tooltip values with no runtime console errors observed.
- Existing Docker files remain functional and unchanged except ignoring new generated folders. The earlier verified ARM64 container remains a separate deployment path.

## Size/dependency evidence

Generated source/data/assets payload: **160 files, 3,771,338 bytes**. Nineteen pinned Linux x86-64 CPython 3.14 runtime wheel contents: **111,660,168 bytes**. Estimated combined payload before provider overhead: **115,431,506 bytes, about 110 MiB**. This is below the standard 500 MB Python limit by measurement/estimate; **it is not a final Vercel-built bundle size**. Provider compilation/packaging must still be inspected after approval.

Sample responses range from about 1.4 KB to 13 KB, below the 4.5 MB function payload cap. Docker's observed roughly 94 MiB idle RAM is encouraging, but does not certify hosted Vercel/Render RAM. Vercel Hobby allows up to 2 GB function memory; Render Free provides 512 MB/0.1 CPU. Current detailed quotas and official sources are in the guide.

## Cold starts and availability

Vercel may cold-start a new instance and load/validate the dataset. Exact provider latency is not measured, and no artificial keep-alive is added. Render Free explicitly sleeps after 15 minutes; first visits may need around one minute and normal retries. Free quotas can pause/suspend service. Neither option guarantees the evaluator immediate or uninterrupted availability.

## Cost controls

Use Vercel **personal Hobby**, not Pro/Enterprise or a trial. Do not add a card, paid add-on, custom domain purchase or integration. Use its free platform domain. If eligibility or usage prevents service, stop rather than pay.

For Render, use a $0 Hobby workspace, explicitly Free compute and **no payment method**. Official docs state that no-payment accounts suspend free services/builds when bandwidth/build quotas are exhausted instead of billing overages. If a card is required for the actual account, stop. Do not assume a paid workspace with a Free service guarantees ₹0.

Under the eligible selected free plan and included limits, **no payment is required**. No provider account state was inspected or changed, no card was added, and no paid resource/upgrade/subscription was enabled. No provider project exists from this work.

## Remaining limits and approval gate

A provider build, final provider bundle size, deployed routing/CDN behavior, hosted cold starts, account eligibility, public readiness and incognito access remain unverified because deployment was explicitly prohibited. The separate CLI Playwright/Scout/amd64 restrictions from earlier phases are not claimed resolved. Existing Vite and Python dependency warnings remain.

`free-deployment-guide.md` contains exact preparation, post-approval CLI steps and public verification. The ready-project ZIP is an isolated Vercel project, not a deployment. The full source ZIP contains the generator/templates and preserved Docker application; generated folders stay ignored. No GitHub publication or form submission occurred.

**Stopped after preparation. Explicit approval is required before any Vercel project creation/deployment or Render Blueprint application.**
