"""Explicit public contracts; all timestamps serialize with UTC offsets."""
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class ErrorDetail(Model):
    code: str
    message: str


class ErrorResponse(Model):
    error: ErrorDetail


class Coverage(Model):
    expected_half_hours: int
    expected_hourly_targets: int
    forecast_observations: int
    actual_observations: int
    matched_observations: int
    missing_hourly_forecasts: int
    missing_half_hour_actuals: int
    structural_half_hour_forecast_gaps: int
    excluded_hourly_pairs: int


class Context(Model):
    unit: Literal['MW'] = 'MW'
    timezone: Literal['Europe/London'] = 'Europe/London'
    cutoff_local: str
    forecast_resolution_minutes: Literal[60] = 60
    actual_resolution_minutes: Literal[30] = 30
    comparison_basis: str = 'Native hourly forecast point versus half-hour mean actual at equal startTime'
    analysis_mode: Literal['retrospective_evaluation'] = 'retrospective_evaluation'
    warnings: list[str]


class DecisionInfo(Model):
    decision_date: date
    delivery_date: date
    decision_cutoff_utc: datetime
    available: bool
    coverage: Coverage


class DecisionsResponse(Context):
    decisions: list[DecisionInfo]


class DayContext(Context):
    decision_date: date
    delivery_date: date
    decision_cutoff_utc: datetime
    coverage: Coverage


class ForecastPoint(Model):
    start_time: datetime
    publish_time: datetime | None
    generation_mw: float | None


class ForecastResponse(DayContext):
    dataset: Literal['WINDFOR'] = 'WINDFOR'
    observations: list[ForecastPoint]


class ActualResponse(DayContext):
    dataset: Literal['FUELHH'] = 'FUELHH'
    fuel_type: Literal['WIND'] = 'WIND'
    actual_revision_policy: str = 'Latest publication in the extracted historical snapshot'
    observations: list[ForecastPoint]


class ComparisonPoint(Model):
    start_time: datetime
    forecast_publish_time: datetime | None
    actual_publish_time: datetime | None
    forecast_mw: float | None
    actual_mw: float | None
    error_mw: float | None
    status: Literal['matched', 'structural_forecast_gap', 'missing_forecast', 'missing_actual', 'missing_both']


class ComparisonResponse(DayContext):
    observations: list[ComparisonPoint]


class Accuracy(Model):
    status: Literal['ok', 'no_matched_observations']
    observation_count: int
    mae_mw: float | None = Field(description='Mean absolute forecast-minus-actual error')
    rmse_mw: float | None = Field(description='Square root of mean squared forecast-minus-actual error')
    bias_mw: float | None = Field(description='Signed mean forecast-minus-actual error; positive means overforecast')
    error_definition: Literal['forecast_mw - actual_mw'] = 'forecast_mw - actual_mw'


class MetricsResponse(Context):
    start_decision_date: date
    end_decision_date: date
    coverage: Coverage
    accuracy: Accuracy
    retrospective_only: Literal[True] = True
