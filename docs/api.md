# Phase 2 backend API

## Start and configure

From the project root:

```sh
source .venv/bin/activate
pip install -r requirements.lock.txt
python -m pipeline.fetch
python -m pipeline.prepare
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs for interactive OpenAPI documentation. The schema is at `/openapi.json`; a snapshot is in `docs/backend-openapi.json`. Nothing is deployed or made public by these commands. All observations come from the preserved Phase 1 raw Elexon extraction, not from synthetic tests.

| Environment variable | Default | Meaning |
|---|---|---|
| `WIND_DATA_ROOT` | project root | Directory containing the complete `data/raw/` extraction and provenance |
| `WIND_DECISION_CUTOFF` | `09:20` | Decision-date cutoff in Europe/London, exact HH:MM |

Invalid configuration fails application creation rather than silently using a default. Every analysis endpoint accepts an optional `cutoff_local=HH:MM` override. The effective cutoff is returned in every response; daily responses include its UTC timestamp. Override changes reselect forecasts from all raw publication vintages, not from a cached alignment file. Publications at exactly the cutoff are excluded.

Example: `/api/decisions/2026-01-01/forecasts?cutoff_local=09:50`. This is an analysis scenario, not a declaration of the customer's actual auction deadline. See the source evidence in `methodology.md` before interpreting any alternative cutoff.

The API validates and loads one immutable raw-data snapshot at startup, including all expected daily files, hashes and original Phase 1 normalization checks. After replacing data, restart the process. No per-request external API calls occur. Incomplete/invalid data causes analysis endpoints to return 503; diagnostic details stay in server logs. The API can load raw data directly; `pipeline.prepare` remains the independent reproducibility/inspection command.

## Endpoints

All routes below are GET. Dates are strictly YYYY-MM-DD calendar dates; allowed decision dates are 2026-01-01 through 2026-01-31 inclusive. Delivery is the following London calendar day, ending on 2026-02-01. UTC timestamps use ISO 8601 with `Z`.

| Path | Response |
|---|---|
| `/api/decisions` | 31 decision dates with delivery date, UTC cutoff, data availability and coverage counts |
| `/api/decisions/{decision_date}/forecasts` | 24 hourly target slots with selected forecast publication and MW, null when unavailable |
| `/api/decisions/{decision_date}/actuals` | 48 half-hour slots with WIND outturn publication and MW, null when unavailable |
| `/api/decisions/{decision_date}/comparisons` | 48 half-hour slots with forecast/actual values, publications, signed error and explicit status |
| `/api/decisions/{decision_date}/metrics` | Retrospective MAE, RMSE, bias and coverage for this decision's next-day targets |
| `/api/metrics?start_date=2026-01-01&end_date=2026-01-31` | Inclusive-range pooled metrics; omitted dates default to the complete January decision month |

`available` means at least one forecast or actual observation exists; it does not promise complete or matched data. A date without any data has `available=false`, and its daily endpoints return 404. Missing pairs within a date remain explicit. Range endpoints retain the expected grid even for dates with no observations, so their coverage counts reveal missing data.

## Response contracts

Common fields: `unit` (MW), `timezone` (Europe/London), effective `cutoff_local`, `forecast_resolution_minutes` (60), `actual_resolution_minutes` (30), `comparison_basis`, `analysis_mode` (retrospective_evaluation), and `warnings`. Daily responses additionally return decision/delivery dates, UTC cutoff and `coverage`.

Forecast and actual observations use `{start_time, publish_time, generation_mw}`. Each value and publication may be null when the native source observation is absent. Forecast responses contain hourly slots only. Actual responses expose `dataset=FUELHH`, `fuel_type=WIND`, and the latest-extracted-publication revision policy.

Comparison observations use `{start_time, forecast_publish_time, actual_publish_time, forecast_mw, actual_mw, error_mw, status}`. For the real 1 January decision, the first two comparison observations are:

```json
[
  {
    "start_time": "2026-01-02T00:00:00Z",
    "forecast_publish_time": "2026-01-01T07:30:00Z",
    "actual_publish_time": "2026-01-02T00:30:00Z",
    "forecast_mw": 18781.0,
    "actual_mw": 15228.0,
    "error_mw": 3553.0,
    "status": "matched"
  },
  {
    "start_time": "2026-01-02T00:30:00Z",
    "forecast_publish_time": null,
    "actual_publish_time": "2026-01-02T01:00:00Z",
    "forecast_mw": null,
    "actual_mw": 15505.0,
    "error_mw": null,
    "status": "structural_forecast_gap"
  }
]
```

This is an observations excerpt, not the complete enclosing response. Complete responses for every route, captured over a running Uvicorn HTTP server, are in `docs/api-samples.json`.

Comparison statuses: `matched`, `structural_forecast_gap` (native :30 slot), `missing_forecast` (hourly forecast missing), `missing_actual`, `missing_both`. On :30 slots, structural status takes precedence; an absent actual is still visible as null and counted in missing actuals. Missing data is never represented by zero.

Coverage fields:

- `expected_half_hours`: full delivery-grid size.
- `expected_hourly_targets`: number of on-hour forecast target slots.
- `forecast_observations`, `actual_observations`: populated native values.
- `matched_observations`: on-hour rows with both values.
- `missing_hourly_forecasts`: absent forecasts on native hourly slots.
- `missing_half_hour_actuals`: absent actuals anywhere on the full grid.
- `structural_half_hour_forecast_gaps`: :30 slots for which no native forecast is defined.
- `excluded_hourly_pairs`: hourly slots missing either value, counted once per slot.

## Accuracy definitions

For each valid on-hour equal-startTime pair, `error = forecast_mw - actual_mw`. With n matched observations:

- MAE = sum(abs(error)) / n, in MW.
- RMSE = sqrt(sum(error²) / n), in MW.
- Bias = sum(error) / n, in MW; positive means wind overforecast.

Range metrics pool observations before calculation; they are not unweighted averages of daily metrics. No percentage errors are used; zero actuals are valid. Missing values are excluded pairwise with counts. With no matched observations, HTTP 200 returns status `no_matched_observations`, observation_count 0 and all three metrics null. This is different from perfect accuracy.

Actual `/api/metrics` accuracy object at default cutoff:

```json
{
  "status": "ok",
  "observation_count": 744,
  "mae_mw": 2022.470430107527,
  "rmse_mw": 2497.407157584179,
  "bias_mw": 1745.9381720430108,
  "error_definition": "forecast_mw - actual_mw"
}
```

Metrics also return `retrospective_only=true` and the inclusive decision-date range. All actuals and errors are historical outcomes: they must never be described as known at that decision date. No forward uncertainty/training endpoint is implemented. Historical January errors are not a decision-time prediction interval for January decisions.

## Errors

Declared analysis errors use `{"error":{"code":"...","message":"..."}}`:

| HTTP | Codes | Meaning |
|---|---|---|
| 422 | `invalid_request` | Invalid date syntax/calendar value or cutoff format/time |
| 422 | `invalid_date_range` | start_date is after end_date |
| 404 | `decision_date_out_of_range` | Outside January decision scope |
| 404 | `decision_data_unavailable` | Daily request has neither forecasts nor actuals |
| 503 | `data_unavailable` | Extraction is absent, incomplete, corrupt or fails validation |

Example actual invalid-cutoff response:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "query.cutoff_local: String should match pattern '^(?:[01][0-9]|2[0-3]):[0-5][0-9]$'"
  }
}
```

Validation message wording may vary with dependency versions; clients should branch on code, not English text. Unknown URLs/methods retain FastAPI's standard 404/405 contracts.

## Architecture and limitations

`backend/main.py` owns startup, dependency configuration and error translation; `routes.py` maps HTTP to services; `models.py` defines Pydantic response contracts; `service.py` orchestrates the original pipeline and response rows; `analytics.py` contains pure statistical calculations; `config.py` validates environment settings. Data parsing/normalization/selection remain in `pipeline/prepare.py`. No database, job queue or extra external service is introduced.

Phase 1 tests are unchanged. Its default output files are byte-for-byte identical after the small refactor extracting `load_sources()` and adding optional cutoff arguments to `cutoff()` and `align()`.

The main limitation remains point-versus-interval semantics: hourly WINDFOR target values are compared to FUELHH's half-hour mean beginning at the same time. This proxy is displayed in every response. No interpolation or assumption of a flat hourly forecast is introduced. These results do not measure full half-hour accuracy, energy-volume errors or procurement costs. The data covers Elexon's represented metered GB wind, not all UK wind or the client's own demand/supply portfolio.

Publication timestamps are availability proxies and do not establish historical client receipt latency or account for late backfills. Actuals use latest revisions present in the historical extraction. The API rejects unexpected non-hourly WINDFOR targets rather than silently changing resolution semantics. Cutoff and intended auction/client operational buffer still require domain confirmation.

Implementation references: [FastAPI multi-file applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/), [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/), [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/). Domain sources remain in the Phase 1 methodology.
