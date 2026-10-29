# Phase 1 methodology and evidence

## Scope and times

The original challenge is the requirements source; the pasted user request defines the approved phased workflow. Only FUELHH (fuelType=WIND) and WINDFOR are used for analysis. National coverage means the GB metered wind represented by these Elexon series, not all UK wind or a utility's own portfolio. Elexon's wind documentation describes wind farms visible to the system operator with operational metering.

Decision dates: 1–31 January 2026 inclusive. Delivery: the following London calendar day, 2 January–1 February. Fetch forecast publications from 25 December 2025 through 31 January 2026 inclusive: seven days of warm-up plus the decision month. Fetch WIND actuals by settlement date for each delivery day. The finite warm-up is a pragmatic bound, not a claim to contain every historic forecast. Coverage checks expose missing eligible targets. No December decision is included.

For each delivery startTime, select the record with maximum publishTime strictly less than 09:20 Europe/London on its decision date. Equality is excluded. This is an explicit EPEX GB hourly-auction scenario based on EPEX's official brochure (09:20 GMT), not a universal GB market rule. Nord Pool's N2EX auction instead closes at 09:50 GMT. The challenge does not identify an exchange or the client's internal deadline. Real procurement would require a safety buffer and confirmed exchange/operational cutoff. January London is UTC; use timezone conversion rather than hard-coding this relationship year-round.

EPEX source: https://www.epexspot.com/sites/default/files/2024-09/Trading%20Brochure%202024%20August.pdf (official indexed brochure; direct web fetch returned 403 during this run).
Alternative-market context: https://www.northsealink.com/en/trade-with-us/register (verify current product rules before changing cutoff).

- publishTime: Elexon-reported forecast publication; availability proxy, not measured client receipt time. Late backfills cannot be reconstructed from a current historic extraction.
- startTime: forecast target or actual interval start, never a publication filter.
- decisionCutoff: London decision date at 09:20, stored in UTC.
- Actual publishTime: separate outturn publication, normally after the interval; allowed to be after the decision because actuals are the retrospective reference, never forecast inputs.

Selection is per target, allowing different publication vintages where needed. Preserve publication information per row. Latest historical actual revision is used; conflicting same-target/same-publication records fail rather than choosing arbitrarily.

## API verification

Official links supplied in the challenge:
- https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream
- https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream

These pages require JavaScript in the research client. The official machine-readable contract was retrieved directly and saved as `elexon-openapi.json`:
https://data.elexon.co.uk/swagger/v1/swagger.json

API base: https://data.elexon.co.uk/bmrs/api/v1

FUELHH stream supports publishDateTimeFrom/To OR settlementDateFrom/To (do not mix), settlementPeriod arrays and fuelType arrays. We request one settlement date at a time, same from/to date, fuelType=WIND. Actual calls returned all 48 January half-hours for a single same-date range.

WINDFOR stream supports publishDateTimeFrom and publishDateTimeTo. Omitting them returns the latest forecast and is unsuitable for a decision-time backtest. Use adjacent daily publication windows. Overlap at inclusive boundaries is harmless because exact duplicate records are counted and removed. Do not rely on undocumented end-boundary exclusivity. Current January forecast publications do not fall at midnight boundaries.

Both stream routes return plain JSON arrays, without a pagination envelope. No page or limit parameters are declared. Elexon's developer portal describes stream endpoints as JSON-only with no data-return restrictions; daily windows are a conservative extraction choice, not an invented seven-day stream limit. The general non-stream dataset APIs also offer CSV/XML; this pipeline does not use them.

https://developer.data.elexon.co.uk/ states that APIs are public with no key required. Actual successful requests supplied no credentials. Contract responses: 200, 400 invalid parameters, 429 too many requests, 500 server error. An intentionally invalid publishDateTimeFrom returned HTTP 400 and `DateTime should be in ISO format`. No numeric request-rate quota was found in the reviewed sources. The client is sequential, uses 60-second timeouts and bounded retries for transport errors/429/selected 5xx, with numeric Retry-After support and exponential fallback. It does not retry invalid queries. HTTP-date Retry-After is not parsed.

## Validation and resolution

FUELHH contract explicitly defines average MW over 30-minute periods. Official developer guidance describes WINDFOR as forecast MW for a specific point in time:
https://developer.data.elexon.co.uk/
https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/latest

Real January WINDFOR targets are hourly, despite the challenge describing startTime as similar to the half-hour actuals. Do not fabricate half-hour forecasts. The aligned file uses a full half-hour delivery grid, joins only equal native startTime values, and retains blank forecast values at :30. Distinguish structural resolution gaps from missing native hourly forecasts. No interpolation, forward-fill or silent averaging is performed.

The exact-start comparison is a transparent preliminary proxy: point-in-time forecast versus the FUELHH half-hour average beginning at that time. It is not an exact match of averaging windows. This limitation must appear with Phase 2 metrics. Hourly mean actuals would introduce another interpretation and should only be used with an explicit product decision and interval-semantics justification. Results cannot claim accuracy for every half-hour or forecast energy volumes.

Normalization requires dataset identity, WIND fuel, aware valid timestamps, finite nonnegative numeric MW, and half-hour target boundaries. Null/invalid data fails visibly; it is never converted to zero. Exact duplicates are removed and counted; conflicting duplicates fail. Revisions are distinct publications for the same target. Raw bytes, retrieval time, full request URL and SHA-256 support audit and reproduction. Each expected daily file is required before preparation. Empty payloads across the extraction fail; partial source gaps are retained and reported.

## Initial comparison and business interpretation

Phase 2 should use valid native timestamp pairs, report sample counts/coverage, and calculate MAE, RMSE and bias with error = forecast minus actual in MW. Positive error means wind was overestimated and could leave a procurement shortfall, all else equal. Negative error means wind was underestimated. No demand, price, cost savings or exact purchase-volume claims can be derived from these two datasets alone.

A retrospective distribution of errors describes historical uncertainty; it is not a calibrated forward prediction interval. Estimating uncertainty for any individual decision must use outcomes known before that decision, not later January outcomes. Do not use full-month retrospective errors as if they were known on 1 January. Fetching prior outcomes/training history, if needed later, remains subject to the two-dataset scope.
