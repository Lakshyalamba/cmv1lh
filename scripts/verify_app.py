"""Verify six endpoints, 31 dates, snapshot metrics and static serving over HTTP.

Run: python -m scripts.verify_app --base-url http://127.0.0.1:8080
"""
import argparse
import json
from urllib.request import urlopen


def verify(base_url):
    def get(path):
        with urlopen(base_url.rstrip('/') + path, timeout=20) as response:
            if response.status != 200:
                raise AssertionError(f'Unexpected status: {path}')
            return json.load(response)
    assert get('/health/live')['status'] == 'live'
    assert get('/health/ready')['status'] == 'ready'
    with urlopen(base_url.rstrip('/') + '/', timeout=20) as r:
        assert 'text/html' in r.headers['Content-Type']
        assert b'type="module"' in r.read()
    dates = get('/api/decisions')['decisions']
    assert len(dates) == 31
    matched = 0
    for day in dates:
        prefix = '/api/decisions/' + day['decision_date']
        forecast, actual, comparison, metrics = [get(prefix + '/' + suffix) for suffix in ['forecasts', 'actuals', 'comparisons', 'metrics']]
        assert len(forecast['observations']) == 24
        assert len(actual['observations']) == len(comparison['observations']) == 48
        errors = []
        for row in comparison['observations']:
            if row['forecast_mw'] is not None:
                assert row['forecast_publish_time'] < comparison['decision_cutoff_utc']
            if row['error_mw'] is not None:
                errors.append(row['error_mw'])
        assert len(errors) == metrics['accuracy']['observation_count']
        matched += len(errors)
    pooled = get('/api/metrics')
    assert matched == pooled['accuracy']['observation_count'] == 744
    return {'decision_dates': len(dates), 'observation_rows': 31 * 48,
            'matched_pairs': matched, 'accuracy': pooled['accuracy'], 'health': 'ready'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8080')
    print(json.dumps(verify(parser.parse_args().base_url), indent=2))
