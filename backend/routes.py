"""HTTP contracts; selection and statistics belong to the service."""
from datetime import date
import re
from pydantic import BeforeValidator
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request
from .models import (ActualResponse, ComparisonResponse, DecisionsResponse,
                     ErrorResponse, ForecastResponse, MetricsResponse)
from .service import DomainError, FIRST, LAST, WindService, comparison_rows, optional

router = APIRouter(prefix='/api', tags=['Wind analysis'], responses={
    404: {'model': ErrorResponse}, 422: {'model': ErrorResponse}, 503: {'model': ErrorResponse}})


def get_service(request: Request) -> WindService:
    if request.app.state.service is None:
        raise DomainError(503, 'data_unavailable', 'Validated data is unavailable. Run pipeline.fetch and pipeline.prepare, then restart the API.')
    return request.app.state.service


def get_cutoff(request: Request, cutoff_local: Annotated[str | None, Query(
    pattern=r'^(?:[01][0-9]|2[0-3]):[0-5][0-9]$',
    description='Strictly-before cutoff, HH:MM Europe/London; defaults to server configuration')] = None) -> str:
    return cutoff_local if cutoff_local is not None else request.app.state.settings.cutoff_local


def calendar_date(value):
    if isinstance(value, str) and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Use a calendar date in YYYY-MM-DD format')
    return value


ISODate = Annotated[date, BeforeValidator(calendar_date)]
Service = Annotated[WindService, Depends(get_service)]
Cutoff = Annotated[str, Depends(get_cutoff)]


@router.get('/decisions', response_model=DecisionsResponse)
def decisions(service: Service, cutoff: Cutoff):
    """All January decision dates, with availability and coverage under the chosen cutoff."""
    return service.decisions(cutoff)


@router.get('/decisions/{decision_date}/forecasts', response_model=ForecastResponse)
def forecasts(decision_date: ISODate, service: Service, cutoff: Cutoff):
    """24 native hourly target slots; missing forecasts are null, never interpolated."""
    frame, context = service.day(decision_date, cutoff)
    frame = frame[frame.startTime.dt.minute.eq(0)]
    return dict(**context, observations=[dict(start_time=r.startTime,
        publish_time=optional(r.forecastPublishTime), generation_mw=optional(r.forecastMw)) for r in frame.itertuples()])


@router.get('/decisions/{decision_date}/actuals', response_model=ActualResponse)
def actuals(decision_date: ISODate, service: Service, cutoff: Cutoff):
    """48 half-hour outturn slots for next-day delivery; historical revisions are retrospective."""
    frame, context = service.day(decision_date, cutoff)
    return dict(**context, observations=[dict(start_time=r.startTime,
        publish_time=optional(r.actualPublishTime), generation_mw=optional(r.actualMw)) for r in frame.itertuples()])


@router.get('/decisions/{decision_date}/comparisons', response_model=ComparisonResponse)
def comparisons(decision_date: ISODate, service: Service, cutoff: Cutoff):
    """48 half-hour grid rows with explicit missingness and signed errors only for matched points."""
    frame, context = service.day(decision_date, cutoff)
    return dict(**context, observations=comparison_rows(frame))


@router.get('/decisions/{decision_date}/metrics', response_model=MetricsResponse)
def day_metrics(decision_date: ISODate, service: Service, cutoff: Cutoff):
    """Retrospective accuracy for one decision's next-day targets."""
    service.day(decision_date, cutoff)
    return service.metrics(decision_date, decision_date, cutoff)


@router.get('/metrics', response_model=MetricsResponse)
def range_metrics(service: Service, cutoff: Cutoff,
                  start_date: ISODate = FIRST, end_date: ISODate = LAST):
    """Pooled, observation-weighted retrospective metrics for an inclusive decision-date range."""
    return service.metrics(start_date, end_date, cutoff)
