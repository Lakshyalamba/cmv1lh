"""Selection orchestration using the original pipeline, never aligned.csv."""
from datetime import date, timedelta
import pandas as pd
from pipeline.prepare import align, cutoff, load_sources
from .analytics import calculate_accuracy, coverage
from .config import Settings, parse_cutoff

FIRST, LAST = date(2026, 1, 1), date(2026, 1, 31)
WARNINGS = [
    'WINDFOR hourly forecast points and FUELHH half-hour averages have different interval semantics.',
    'No interpolation: :30 forecast gaps are structural; metrics use native equal-startTime pairs only.',
    'Actuals and errors are retrospective outcomes, not information available at the decision cutoff.',
    'Publication time is an availability proxy; historical backfills and client receipt latency are unknown.',
    'The cutoff is a configurable auction scenario, not a universal GB procurement deadline.',
    'Historical errors are not calibrated prediction intervals or purchase-volume recommendations.',
]


class DomainError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


class WindService:
    def __init__(self, forecasts, actuals, settings: Settings):
        self.settings = settings
        if not forecasts.startTime.dt.minute.eq(0).all():
            raise ValueError('WINDFOR resolution changed; review methodology before serving')
        self.forecasts = forecasts.copy()
        self.actuals = actuals.copy()

    @classmethod
    def load(cls, settings):
        frames, _ = load_sources(settings.data_root)
        return cls(frames['WINDFOR'], frames['FUELHH'], settings)

    def context(self, cutoff_local):
        return dict(cutoff_local=cutoff_local, warnings=WARNINGS.copy())

    def aligned(self, start, end, cutoff_local):
        if start > end:
            raise DomainError(422, 'invalid_date_range', 'start_date must be on or before end_date')
        if start < FIRST or end > LAST:
            raise DomainError(404, 'decision_date_out_of_range', 'Decision dates must be within 2026-01-01 through 2026-01-31')
        return align(self.forecasts, self.actuals, start, end, cutoff_time=parse_cutoff(cutoff_local))

    def day(self, decision_date, cutoff_local):
        frame = self.aligned(decision_date, decision_date, cutoff_local)
        if not frame[['forecastMw', 'actualMw']].notna().any().any():
            raise DomainError(404, 'decision_data_unavailable', 'No forecast or actual observations for this decision date')
        context = dict(**self.context(cutoff_local), decision_date=decision_date,
                       delivery_date=decision_date + timedelta(days=1),
                       decision_cutoff_utc=cutoff(decision_date, parse_cutoff(cutoff_local)),
                       coverage=coverage(frame))
        return frame, context

    def decisions(self, cutoff_local):
        frame = self.aligned(FIRST, LAST, cutoff_local)
        decisions = []
        for day, group in frame.groupby('decisionDate', sort=True):
            day = date.fromisoformat(day)
            decisions.append(dict(decision_date=day, delivery_date=day + timedelta(days=1),
                decision_cutoff_utc=cutoff(day, parse_cutoff(cutoff_local)),
                available=bool(group[['forecastMw', 'actualMw']].notna().any().any()), coverage=coverage(group)))
        return dict(**self.context(cutoff_local), decisions=decisions)

    def metrics(self, start, end, cutoff_local):
        frame = self.aligned(start, end, cutoff_local)
        return dict(**self.context(cutoff_local), start_decision_date=start, end_decision_date=end,
                    coverage=coverage(frame), accuracy=calculate_accuracy(frame))


def optional(value):
    return None if pd.isna(value) else value


def comparison_rows(frame):
    rows = []
    for r in frame.itertuples():
        f, a = optional(r.forecastMw), optional(r.actualMw)
        if r.startTime.minute != 0:
            status = 'structural_forecast_gap'
        elif f is None and a is None:
            status = 'missing_both'
        elif f is None:
            status = 'missing_forecast'
        elif a is None:
            status = 'missing_actual'
        else:
            status = 'matched'
        rows.append(dict(start_time=r.startTime, forecast_publish_time=optional(r.forecastPublishTime),
                         actual_publish_time=optional(r.actualPublishTime), forecast_mw=f, actual_mw=a,
                         error_mw=optional(r.errorMw), status=status))
    return rows
