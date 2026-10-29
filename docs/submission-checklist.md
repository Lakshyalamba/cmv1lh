# Final submission checklist — nothing submitted

The original challenge requires React + Python, Docker, only the specified Elexon wind data, January 2026 purchase decisions, a Vercel/Heroku sample app, a public GitHub repository with an anonymous/random name, an unlisted two-part YouTube video and the Microsoft form. Maximum total effort: 16 hours; no deadline specified. The employer starts evaluation with the video: do not submit without it.

## Current delivery record

| Deliverable | Status | Actual URL |
|---|---|---|
| Public application | Deployed on Vercel Hobby | https://cmv1lh.vercel.app |
| Public anonymous GitHub repo | Publication authorized; verify public URL before submission | https://github.com/Lakshyalamba/cmv1lh |
| Unlisted video | Script prepared; not recorded/uploaded | Not yet available |
| Submission form | Not submitted | https://forms.cloud.microsoft/r/FTX6K2bbnU |

## Before publication

- [ ] Approve the ₹0-only deployment architecture. Do not enable any recurring cost, payment method or paid fallback; see free-deployment.md.
- [ ] Complete platform-specific packaging/build verification. For Heroku, build/run linux/amd64; local ARM64 success alone is insufficient.
- [ ] Complete or explicitly review the blocked image vulnerability scan and command-line browser checks.
- [ ] Review sanitized source, final README and attribution. Confirm no owner paths, secrets, credentials or unnecessary generated artifacts are staged.
- [ ] Approve the short random repository name shown in the final report. The GitHub account owner will still be visible in its URL; random naming does not anonymize the account.
- [ ] Decide whether an application-code licence is desired. No new licence was assigned automatically. Preserve Elexon and third-party notices regardless.
- [ ] Verify source snapshot and lockfiles from a clean checkout; retain `data/snapshot.tar.gz` and its hash, but not local raw caches or environments.

## Application URL

- [ ] Give explicit authorization before creating/deploying public resources.
- [ ] Record the actual HTTPS application URL after success; add it to README.
- [ ] Confirm public readiness, frontend assets and all six API route types using `scripts.verify_app`.
- [ ] Verify all 31 dates, clear GMT/MW labels, hourly/half-hour limitation, counts and selected publication times.
- [ ] In a private/incognito session, check the app without provider authentication or deployment protection. Do not bypass a security warning; fix the deployment instead.

## GitHub URL

- [ ] Give explicit authorization before publication.
- [ ] Create a **public** repository with the approved anonymous/random name; do not put the candidate/company name in the repository name.
- [ ] Inspect staged files and commit metadata before pushing. Choose intended author identity; no personal Git identity was inserted by this preparation.
- [ ] Confirm README overview, structure, startup commands, real public app URL and AI disclosure are present.
- [ ] In incognito, open the repo, view source and download/clone it without authentication.

## Video URL

- [ ] Record the customer presentation, at most 5 minutes.
- [ ] Record the technical review, at most 5 minutes; total video at most 10 minutes.
- [ ] Show the working app and correct actual metrics; explain cutoff/resolution assumptions and honest AI use.
- [ ] Remove private notifications, account information and local owner paths.
- [ ] Give explicit authorization before uploading; use **Unlisted**, not Private.
- [ ] In incognito, open the watch URL and play both parts without login or an access request.

## Final form gate

- [ ] Re-check all three real URLs in incognito after the final changes.
- [ ] Confirm employer requirements individually: only Elexon WINDFOR/FUELHH WIND, January decision scope, React/Python, Docker, Vercel/Heroku hosting, random public repo, README app link/structure/startup/AI disclosure, unlisted two-part <=10-minute video.
- [ ] Confirm candidate total effort remains within 16 hours, including human review, recording and deployment.
- [ ] Review the Microsoft form fields before submitting; no assumptions about unseen required fields are made here.
- [ ] Obtain explicit final submission authorization, then submit https://forms.cloud.microsoft/r/FTX6K2bbnU.
- [ ] Record actual submission confirmation only if the form is successfully submitted.

**Current state is preparation, not fulfillment of every employer deliverable.** Hosting is deployed; verify repository publication and complete the video and form only with their respective authorizations. Do not mark these items complete or invent URLs.
