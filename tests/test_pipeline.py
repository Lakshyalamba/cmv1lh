from datetime import date
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import patch
import pytest
from pipeline.fetch import request_json
from pipeline.prepare import normalize, align, cutoff


def row(dataset='WINDFOR', start='2026-01-02T00:00:00Z', publish='2026-01-01T08:30:00Z', value=100):
    r = dict(dataset=dataset, startTime=start, publishTime=publish, generation=value)
    if dataset == 'FUELHH':
        r['fuelType'] = 'WIND'
    return r


def test_cutoff_and_revisions():
    f, _ = normalize([row(value=100), row(publish='2026-01-01T09:19:59Z', value=110),
                      row(publish='2026-01-01T09:20:00Z', value=999),
                      row(publish='2026-01-01T10:30:00Z', value=900)], 'WINDFOR')
    a, _ = normalize([row('FUELHH', publish='2026-01-02T00:30:00Z', value=105)], 'FUELHH')
    out = align(f, a, date(2026, 1, 1), date(2026, 1, 1))
    assert len(out) == 48
    assert out.iloc[0].forecastMw == 110
    assert out.iloc[0].errorMw == 5
    assert out.forecastMw.isna().sum() == 47
    assert str(cutoff(date(2026, 1, 1))) == '2026-01-01 09:20:00+00:00'
    assert cutoff(date(2026, 7, 1)).hour == 8


def test_duplicates_and_conflicts():
    f, stats = normalize([row(), row()], 'WINDFOR')
    assert len(f) == 1 and stats['exact_duplicates_removed'] == 1
    with pytest.raises(ValueError, match='conflicting'):
        normalize([row(), row(value=101)], 'WINDFOR')


@pytest.mark.parametrize('value', [None, -1, float('inf'), 'invalid'])
def test_invalid_generation(value):
    with pytest.raises((ValueError, TypeError)):
        normalize([row(value=value)], 'WINDFOR')


def test_invalid_timestamps_and_dataset():
    for r in [row(start='2026-01-02T00:00:00'), row(start='garbage'),
              row(start='2026-01-02T00:01:00Z'), row(dataset='OTHER')]:
        with pytest.raises(ValueError):
            normalize([r], 'WINDFOR')
    r = row('FUELHH'); r['fuelType'] = 'CCGT'
    with pytest.raises(ValueError):
        normalize([r], 'FUELHH')
    with pytest.raises(ValueError):
        normalize([], 'WINDFOR')


def test_actual_revisions_and_delivery_boundaries():
    f, _ = normalize([row(), row(start='2026-01-03T00:00:00Z')], 'WINDFOR')
    a, _ = normalize([row('FUELHH', value=80), row('FUELHH', publish='2026-02-01T00:00:00Z', value=90)], 'FUELHH')
    out = align(f, a, date(2026, 1, 1), date(2026, 1, 1))
    assert out.iloc[0].actualMw == 90
    assert out.forecastMw.notna().sum() == 1


def test_http_retry_and_fatal_errors():
    transient = HTTPError('url', 429, 'slow down', {'Retry-After': '1'}, None)
    with patch('pipeline.fetch.urlopen', side_effect=[transient, BytesIO(b'[]')]), patch('pipeline.fetch.time.sleep') as sleep:
        assert request_json('https://example.test')[1] == []
        sleep.assert_called_once_with(1)
    with patch('pipeline.fetch.urlopen', side_effect=HTTPError('url', 400, 'bad query', {}, None)):
        with pytest.raises(HTTPError):
            request_json('https://example.test')
    with patch('pipeline.fetch.urlopen', return_value=BytesIO(b'{"data":[]}')):
        with pytest.raises(ValueError):
            request_json('https://example.test')


def test_incomplete_extraction_fails(tmp_path):
    with patch('pipeline.prepare.ROOT', tmp_path):
        from pipeline.prepare import main
        with pytest.raises(ValueError, match='Incomplete extraction'):
            main()


def test_retry_exhaustion():
    with patch('pipeline.fetch.urlopen', side_effect=TimeoutError('timeout')), patch('pipeline.fetch.time.sleep') as sleep:
        with pytest.raises(TimeoutError):
            request_json('https://example.test', attempts=3)
        assert sleep.call_count == 2
