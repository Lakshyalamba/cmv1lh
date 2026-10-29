> Current status: deployed on Vercel Hobby at https://cmv1lh.vercel.app. Vercel Support confirmed eligibility for the unpaid personal hiring demonstration. The original assessment and preparation steps below are retained as historical context; no paid resources were enabled.

# ₹0-only deployment configuration

**Current decision:** the Heroku Basic recommendation is cancelled. No subscription, paid resource, add-on, custom domain purchase, trial-to-paid upgrade or payment method is authorized.

**Preferred candidate:** one **Vercel Hobby personal project**, for the user's confirmed **unpaid personal hiring-evaluation demo**. The app is not a company-operated utility service and will not sell products, accept payments or advertise services. This is an eligibility inference from the stated facts, not written Vercel approval or an explicit hiring-assignment exemption. If account onboarding, current terms or Vercel support indicate ineligibility, stop; never solve it by upgrading. Render Free is prepared as the zero-cost fallback.

The original challenge names Vercel or Heroku. Vercel matches that hosting requirement. **Render is the user's newly authorized alternative, but is not one of the employer's named hosts**; obtain employer acceptance if using it for the final submission. No messages were sent to the employer/provider.

## Official limits and eligibility review

Checked 29 October 2026; provider quotas/terms can change. Only the linked primary sources support the plan.

| Item | Vercel Hobby | Render Free on a Hobby workspace |
|---|---|---|
| Charge within included limits | $0, personal/non-commercial scope | $0 compute when explicitly selecting Free; workspace Hobby is $0 |
| Runtime | Python 3.14 supported; FastAPI lifespan supported | Existing Docker web service, platform-assigned PORT |
| Runtime RAM | Hobby function maximum 2 GB | 512 MB / 0.1 CPU |
| Function/request time | Hobby maximum 300 seconds; prepared function capped at 60 seconds | Render documents HTTP responses up to 100 minutes; service CPU/memory/health limits still apply |
| Bundle/build | Standard Python function limit 500 MB uncompressed; build timeout 45 minutes | Hobby build pipeline: 500 minutes/month, Starter build tier 2 CPU/8 GB. No separate free Git/Docker-build size limit was found in reviewed pages; the 10 GB compressed limit is documented for prebuilt images |
| Transfer and compute quotas | 100 GB fast transfer, 10 GB origin transfer; 1 million function invocations, 4 CPU-hours and 360 GB-hours provisioned memory included | New Hobby workspace: 5 GB outbound bandwidth/month; 750 shared Free instance-hours/month |
| Cold behavior | A new function instance loads Python/dependencies and validates the immutable snapshot. No fixed cold-start duration or always-warm guarantee | Spins down after 15 idle minutes; documented wake-up around one minute, potentially variable |
| Overage consequence | Hobby quotas can pause/restrict service; do not upgrade to paid usage | With no payment method, exhausted bandwidth suspends free services; exhausted build minutes disables new builds; free-hour exhaustion suspends services |
| Persistent disk/database | Not needed; source data must be bundled read-only | No persistent disk on Free; baked image data survives instance replacement; no database needed |

Vercel restricts Hobby to non-commercial personal use and describes commercial purpose broadly, including financial gain and paid creation/hosting. The official examples do not specifically decide unpaid hiring assignments. The user's unpaid/personal confirmation supports the intended demo classification; **do not repurpose this deployment as the company's operational product**. Ask Vercel support if that classification remains uncertain, without authorizing a paid fallback.

Render's reviewed Free documentation recommends Free for testing/hobby/preview use and says not to use it for production applications. It does not state the same Vercel Hobby commercial-use test in those Free-plan pages; Render's general terms still apply. A preview deployment is not an SLA-backed utility production service on either provider.

### Primary references

- [Vercel Hobby quotas and use restrictions](https://vercel.com/docs/plans/hobby)
- [Vercel fair-use commercial examples and support guidance](https://vercel.com/docs/limits/fair-use-guidelines)
- [Vercel Python versions, bundling and relative files](https://vercel.com/docs/functions/runtimes/python)
- [Vercel FastAPI entry points/static assets/lifespan](https://vercel.com/docs/frameworks/backend/fastapi)
- [Vercel function memory/duration/payload limits](https://vercel.com/docs/functions/limitations)
- [Vercel build limits](https://vercel.com/docs/limits)
- [Render Free lifecycle, hours and no-card exhaustion behavior](https://render.com/docs/free)
- [Render current Hobby bandwidth](https://render.com/docs/new-workspace-plans)
- [Render build pipeline limits and no-payment behavior](https://render.com/docs/build-pipeline)
- [Render compute plans](https://render.com/docs/compute-plans)
- [Render HTTP request duration comparison](https://render.com/docs/render-vs-vercel-comparison)
- [Render prebuilt-image size](https://render.com/docs/deploying-an-image)
- [Render Blueprint schema](https://render.com/docs/blueprint-spec)

## Vercel implementation

The Docker application and analytical code are unchanged. `scripts/prepare_vercel.py` creates an isolated `.deploy/vercel/` project containing:

- `app.py`: a small Vercel-only entry point calling the existing `create_app`, with bundle-relative data/static paths. Six existing analysis routes and statistics are reused.
- `requirements.txt`: exact 19-package runtime lock, excluding pytest/HTTPX/dev dependencies.
- `.python-version`: explicitly `3.14`; Vercel's default 3.12 is not relied on.
- `backend/`, `pipeline/`, original expanded `data/raw/` with all 138 JSON/provenance files, and the built `static/` assets.
- `vercel.json`: FastAPI framework, explicit source/data/static inclusion and a 60-second function limit. No paid service declarations.
- Data/software notices. No environment secrets, virtualenv, node_modules, test reports or personal paths are packaged.

The build preparation checks the snapshot SHA-256 before extraction and runs the original `load_sources` checks afterwards. Extraction is **local/build-time**, never into Vercel's read-only runtime source. All data and generation values are unchanged. Python may read bundled files; the adapter does not require a persistent writable directory. Cold instances reconstruct in-memory frames from the same included snapshot.

The prepared app serves both the built React root/assets and `/api` from one FastAPI project. Relative API URLs therefore need no CORS change or second service. Provider static promotion/CDN behavior and function routing still require the actual Vercel build/public smoke test. Local ASGI verification does not certify the Vercel router.

The source payload is about **3.8 MB** before dependencies. The 19 resolved Linux x86-64 CPython 3.14 wheels contain **111,660,168 uncompressed bytes (106.5 MiB)**. Adding the measured source payload gives an estimate around **110 MiB**, below the standard 500 MB Python limit. Provider bytecode/packaging overhead is not included: **a final Vercel bundle size has not been measured**. No 5 GB beta, paid large-function capability or extra compute plan is needed or enabled by this configuration. Runtime RAM must still be monitored; the existing local ARM64 container was observed around 94 MiB at idle, which is not a Vercel memory measurement.

A fresh function may cold-start and validate the dataset; exact latency is unmeasured. The frontend has a 20-second request timeout with retry. Open the app normally before recording and let readiness complete; do not add anti-sleep/keep-alive traffic to evade provider limits. For independent evaluators, disclose that the first visit may take longer. Free quotas provide no guaranteed availability window.

### Prepare and inspect locally

From the project root:

```sh
# Existing Python 3.14 environment is needed for snapshot validation.
source .venv/bin/activate
npm ci --prefix frontend
npm run build --prefix frontend
python -m scripts.prepare_vercel
# Optional isolated ASGI check; this is NOT a provider deployment.
cd .deploy/vercel
../../.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8081
```

In another terminal, from project root:

```sh
source .venv/bin/activate
python -m scripts.verify_app --base-url http://127.0.0.1:8081
```

Generated output is ignored by Git/Docker. Re-run preparation after source/build changes. A future local `.vercel` project link is preserved by the preparer and omitted from the payload manifest. It does not create/link a project, authenticate, publish or call the Vercel CLI.

### Deployment steps — execute only after explicit approval

1. Review the Hobby eligibility inference and current terms. Use a **personal Hobby** account, with no company/Pro team scope. Do not start a Pro trial or add a payment method. If Hobby is unavailable/ineligible, stop and use the separately approved Render Free fallback instead of paying.
2. Rebuild the frontend and regenerate `.deploy/vercel`; inspect its manifest and original data hash.
3. Install the official Vercel CLI locally if needed, then authenticate. Creating/linking the project and sending source are deployment actions and remain unexecuted.
4. From `.deploy/vercel`, run `vercel --prod` **only after approval**. Answer project prompts interactively: new single project, personal Hobby scope, FastAPI detected, no paid integrations. Do not use `--yes` blindly. The project directory already contains built assets and the runtime requirements.
5. Keep `WIND_DECISION_CUTOFF=09:20` if setting an explicit environment value. Do not set Docker's `/app` data/static paths or a frontend external API URL. No API keys, databases, storage add-ons or custom domains are needed. Use the included free `vercel.app` domain.
6. Inspect the provider build logs for Python 3.14, dependency installation, file inclusion and bundle size. A local prepare/ASGI pass is not this provider-build pass. Do not upgrade to resolve a failure.
7. Check the returned HTTPS `/health/ready`, `/`, `/assets/*` and all six APIs. Run `scripts.verify_app` against the actual returned URL, select all dates and inspect charts/metrics/console. Verify anonymously in incognito without deployment protection blocking the reviewer. If account policy cannot expose the demo freely, stop; do not buy an upgrade.
8. Monitor Hobby quotas. If service pauses, leave it paused or remove the deployment; do not enable paid continuation. Only then insert the real URL into README.

## Render Free fallback

`render.yaml` explicitly sets **`plan: free`**. This matters: the official Blueprint reference defaults new services to a paid plan if `plan` is omitted. It reuses the existing `backend/Dockerfile` and root build context, `/health/ready`, platform PORT and same-origin application. Auto-deploys are off to reduce accidental build-quota use. No database, disk, paid instance, private registry, cron or custom domain is declared.

After separate approval, use a **Hobby workspace with no payment method**. Create a Web Service from the approved source/repository, choose Docker and the Free instance, or apply the reviewed Blueprint. Verify that every displayed recurring total is $0 before creation. Use the free `onrender.com` domain. If Render requires a card or paid resource for this account, stop. Do not switch to Starter/paid compute, enable paid workspace features or attach storage.

The original data stays in the image; sleeping/restarts do not require an external Elexon request or database. The existing Docker image is small compared with the documented prebuilt-image cap, but no Render builder run, amd64 image execution or hosted 512 MB measurement has occurred here. Render will build from the Dockerfile on its own infrastructure; inspect build logs and run the same public verifier after deployment.

Warn reviewers about **15-minute inactivity sleep and approximately one-minute wake-up**; actual wake-up can vary. Let the landing page finish waking before the demo. Backend requests during wake-up may exceed the frontend's timeout; wait and retry normally. Do not claim always-on availability. Do not use artificial keep-alive services to work around Free behavior.

Render's Free plan can charge bandwidth/build overages if a payment method is present. **Do not add one**: official docs state that without it exhausted allowances suspend services/builds instead. If the intended account already has billing enabled, do not deploy until a genuinely no-payment arrangement is reviewed. Remaining free hours and bandwidth are workspace-shared.

## Cost confirmation and stop point

The selected configuration requires **no payment under the eligible free plan and included limits**. No subscription, card, paid resource, upgrade or add-on was purchased/enabled. This is not an unlimited-availability promise: quota exhaustion or eligibility failure may block service, and the ₹0 instruction means stopping rather than paying.

No provider build, deployment, GitHub publication or assignment submission has occurred. Approval is still required before creating the Vercel project or applying Render configuration.
