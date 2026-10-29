from datetime import date
import math
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from backend.analytics import calculate_accuracy
from backend.config import Settings
from backend.main import create_app
from backend.service import WindService
from pipeline.prepare import normalize


def record(dataset, start, generation, publish):
    r = dict(dataset=dataset, startTime=f'2026-01-02T{start}:00Z',
             publishTime=publish, generation=generation)
    if dataset == 'FUELHH':
        r['fuelType'] = 'WIND'
    return r


@pytest.fixture
def service():
    forecast = [record('WINDFOR', '00:00', 12, '2026-01-01T08:30:00Z'),
                record('WINDFOR', '01:00', 16, '2026-01-01T08:30:00Z'),
                record('WINDFOR', '00:00', 999, '2026-01-01T09:20:00Z'),
                record('WINDFOR', '01:00', 888, '2026-01-01T09:30:00Z')]
    actual = [record('FUELHH', t, g, '2026-01-03T00:00:00Z')
              for t, g in [('00:00', 10), ('00:30', 11), ('01:00', 20), ('01:30', 25)]]
    f, _ = normalize(forecast, 'WINDFOR')
    a, _ = normalize(actual, 'FUELHH')
    return WindService(f, a, Settings())


@pytest.fixture
def client(service):
    with TestClient(create_app(service=service)) as client:
        yield client


def test_metrics_hand_calculated(client):
    response = client.get('/api/decisions/2026-01-01/metrics')
    assert response.status_code == 200
    body = response.json()
    metrics = body['accuracy']
    assert metrics['observation_count'] == 2
    assert metrics['mae_mw'] == 3
    assert metrics['rmse_mw'] == pytest.approx(math.sqrt(10))
    assert metrics['bias_mw'] == -1
    assert body['unit'] == 'MW' and body['retrospective_only'] is True
    assert body['coverage'] == dict(expected_half_hours=48, expected_hourly_targets=24,
        forecast_observations=2, actual_observations=4, matched_observations=2,
        missing_hourly_forecasts=22, missing_half_hour_actuals=44,
        structural_half_hour_forecast_gaps=24, excluded_hourly_pairs=22)


def test_forecast_actual_comparison_contracts(client):
    f = client.get('/api/decisions/2026-01-01/forecasts').json()
    a = client.get('/api/decisions/2026-01-01/actuals').json()
    c = client.get('/api/decisions/2026-01-01/comparisons').json()
    assert len(f['observations']) == 24 and len(a['observations']) == 48
    assert len(c['observations']) == 48
    assert f['observations'][0]['generation_mw'] == 12
    assert f['observations'][0]['publish_time'] == '2026-01-01T08:30:00Z'
    assert a['observations'][0]['generation_mw'] == 10
    assert c['observations'][0]['error_mw'] == 2
    assert c['observations'][1]['forecast_mw'] is None
    assert c['observations'][1]['status'] == 'structural_forecast_gap'
    assert c['observations'][1]['error_mw'] is None
    assert c['observations'][4]['status'] == 'missing_both'
    assert c['forecast_resolution_minutes'] == 60 and c['actual_resolution_minutes'] == 30
    assert c['delivery_date'] == '2026-01-02'
    assert c['decision_cutoff_utc'] == '2026-01-01T09:20:00Z'


def test_configurable_cutoff_excludes_equal_publications(client):
    early = client.get('/api/decisions/2026-01-01/forecasts?cutoff_local=08:30').json()
    assert early['coverage']['forecast_observations'] == 0
    exact = client.get('/api/decisions/2026-01-01/forecasts?cutoff_local=09:30').json()
    assert exact['observations'][0]['generation_mw'] == 999
    assert exact['observations'][1]['generation_mw'] == 16  # 09:30 publication excluded
    later = client.get('/api/decisions/2026-01-01/forecasts?cutoff_local=09:31').json()
    assert later['observations'][1]['generation_mw'] == 888
    assert later['cutoff_local'] == '09:31'


def test_zero_pairs_are_null_not_zero(client):
    body = client.get('/api/decisions/2026-01-01/metrics?cutoff_local=00:00').json()
    assert body['accuracy']['status'] == 'no_matched_observations'
    assert body['accuracy']['observation_count'] == 0
    assert all(body['accuracy'][key] is None for key in ['mae_mw', 'rmse_mw', 'bias_mw'])


def test_dates_and_range_metrics(client):
    body = client.get('/api/decisions').json()
    assert len(body['decisions']) == 31
    assert body['decisions'][0]['available'] is True
    assert body['decisions'][1]['available'] is False
    assert body['decisions'][-1]['delivery_date'] == '2026-02-01'
    pooled = client.get('/api/metrics').json()
    assert pooled['accuracy']['observation_count'] == 2
    assert pooled['accuracy']['bias_mw'] == -1
    assert pooled['coverage']['expected_half_hours'] == 1488
    day = client.get('/api/metrics?start_date=2026-01-01&end_date=2026-01-01').json()
    assert day['accuracy'] == pooled['accuracy']


@pytest.mark.parametrize('path,status,code', [
    ('/api/decisions/not-a-date/metrics', 422, 'invalid_request'),
    ('/api/decisions/2026-02-30/forecasts', 422, 'invalid_request'),
    ('/api/decisions/2025-12-31/actuals', 404, 'decision_date_out_of_range'),
    ('/api/decisions/2026-02-01/comparisons', 404, 'decision_date_out_of_range'),
    ('/api/decisions/2026-01-02/metrics', 404, 'decision_data_unavailable'),
    ('/api/metrics?start_date=2026-01-03&end_date=2026-01-01', 422, 'invalid_date_range'),
    ('/api/metrics?start_date=2026-01-01T00:00:00Z', 422, 'invalid_request'),
    ('/api/metrics?cutoff_local=24:00', 422, 'invalid_request'),
    ('/api/metrics?cutoff_local=9:20', 422, 'invalid_request'),
    ('/api/metrics?cutoff_local=09:20:00', 422, 'invalid_request'),
    ('/api/metrics?cutoff_local=09:20Z', 422, 'invalid_request'),
])
def test_errors(client, path, status, code):
    response = client.get(path)
    assert response.status_code == status
    assert response.json()['error']['code'] == code
    assert response.json()['error']['message']


def test_missing_data_returns_503(tmp_path):
    with TestClient(create_app(Settings(data_root=tmp_path))) as c:
        response = c.get('/api/decisions')
        assert response.status_code == 503
        assert response.json()['error']['code'] == 'data_unavailable'
        assert str(tmp_path) not in response.text


def test_env_configuration(monkeypatch, service):
    monkeypatch.setenv('WIND_DECISION_CUTOFF', '08:30')
    settings = Settings.from_env()
    with TestClient(create_app(settings=settings, service=service)) as c:
        assert c.get('/api/decisions/2026-01-01/forecasts').json()['coverage']['forecast_observations'] == 0
    monkeypatch.setenv('WIND_DECISION_CUTOFF', '25:00')
    with pytest.raises(ValidationError):
        Settings.from_env()


@pytest.mark.parametrize('forecasts,actuals,expected', [
    ([0], [0], (0, 0, 0)), ([10], [0], (10, 10, 10)),
    ([0], [5], (5, 5, -5)), ([2, 4], [1, 3], (1, 1, 1)),
    ([2, np.nan], [1, 500], (1, 1, 1))])
def test_calculation_edge_cases(forecasts, actuals, expected):
    frame = pd.DataFrame({'startTime': pd.date_range('2026-01-02', periods=len(forecasts), freq='h', tz='UTC'),
                          'forecastMw': forecasts, 'actualMw': actuals})
    result = calculate_accuracy(frame)
    assert (result.mae_mw, result.rmse_mw, result.bias_mw) == expected


def test_nonfinite_metrics_fail():
    frame = pd.DataFrame({'startTime': [pd.Timestamp('2026-01-02', tz='UTC')],
                          'forecastMw': [float('inf')], 'actualMw': [0]})
    with pytest.raises(ValueError, match='finite'):
        calculate_accuracy(frame)


def test_missing_actual_and_missing_forecast(service):
    service.actuals = service.actuals[service.actuals.startTime.dt.hour.ne(1)]
    service.forecasts = service.forecasts[service.forecasts.startTime.dt.hour.ne(0)]
    with TestClient(create_app(service=service)) as c:
        rows = c.get('/api/decisions/2026-01-01/comparisons').json()['observations']
        assert rows[0]['status'] == 'missing_forecast'
        assert rows[2]['status'] == 'missing_actual'
        assert rows[0]['error_mw'] is None and rows[2]['error_mw'] is None
        assert c.get('/api/decisions/2026-01-01/metrics').json()['accuracy']['observation_count'] == 0


def test_pooled_metrics_are_observation_weighted(service):
    # Two observations on day one, one on day two. Mean daily MAEs would be incorrect.
    f = service.forecasts.iloc[[0]].copy(); f['startTime'] += pd.Timedelta(days=1); f['generation'] = 100
    a = service.actuals.iloc[[0]].copy(); a['startTime'] += pd.Timedelta(days=1); a['generation'] = 0
    service.forecasts = pd.concat([service.forecasts, f], ignore_index=True)
    service.actuals = pd.concat([service.actuals, a], ignore_index=True)
    result = service.metrics(date(2026, 1, 1), date(2026, 1, 2), '09:20')['accuracy']
    assert result.observation_count == 3
    assert result.mae_mw == pytest.approx(106 / 3)
    assert result.bias_mw == pytest.approx(98 / 3)


def test_openapi_has_contracts(client):
    schema = client.get('/openapi.json').json()
    assert len(schema['paths']) == 6
    assert schema['components']['schemas']['Accuracy']['properties']['bias_mw']['description']
    assert '503' in schema['paths']['/api/metrics']['get']['responses']
