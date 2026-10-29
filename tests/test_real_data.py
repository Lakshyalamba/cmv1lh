"""Optional real-snapshot integration tests; unit tests remain self-contained."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
from fastapi.testclient import TestClient
import pytest
from backend.config import Settings
from backend.main import create_app
from pipeline.fetch import ROOT

pytestmark = pytest.mark.skipif(not (ROOT / 'data/raw/WINDFOR-2026-01-01.json').exists(),
                                reason='Run pipeline.fetch to enable real-data integration tests')


def test_real_api_against_independent_source_oracle():
    # Standard-library oracle does not call align(), pandas or backend analytics.
    by_target, actuals = {}, {}
    for dataset in ['WINDFOR', 'FUELHH']:
        for path in (ROOT / 'data/raw').glob(f'{dataset}-*.json'):
            if path.name.endswith('.meta.json'):
                continue
            for r in json.loads(path.read_bytes()):
                target = datetime.fromisoformat(r['startTime'])
                published = datetime.fromisoformat(r['publishTime'])
                if dataset == 'WINDFOR':
                    by_target.setdefault(target, []).append((published, r['generation']))
                else:
                    if target not in actuals or published > actuals[target][0]:
                        actuals[target] = (published, r['generation'])
    errors = []
    with TestClient(create_app()) as client:
        decisions = client.get('/api/decisions').json()['decisions']
        assert len(decisions) == 31 and all(d['available'] for d in decisions)
        for d in decisions:
            decision_date = d['decision_date']
            cutoff = datetime.fromisoformat(d['decision_cutoff_utc'])
            response = client.get(f'/api/decisions/{decision_date}/comparisons')
            assert response.status_code == 200
            for r in response.json()['observations']:
                target = datetime.fromisoformat(r['start_time'])
                assert r['actual_mw'] == actuals[target][1]
                if target.minute == 30:
                    assert r['forecast_mw'] is None and r['error_mw'] is None
                    continue
                eligible = [(p, g) for p, g in by_target[target] if p < cutoff]
                latest = max(eligible, key=lambda row: row[0])
                assert datetime.fromisoformat(r['forecast_publish_time']) == latest[0]
                assert r['forecast_mw'] == latest[1]
                errors.append(latest[1] - actuals[target][1])
        result = client.get('/api/metrics').json()
        assert len(errors) == result['accuracy']['observation_count'] == 744
        assert result['accuracy']['mae_mw'] == pytest.approx(sum(map(abs, errors)) / len(errors))
        assert result['accuracy']['rmse_mw'] == pytest.approx(math.sqrt(sum(e * e for e in errors) / len(errors)))
        assert result['accuracy']['bias_mw'] == pytest.approx(sum(errors) / len(errors))
        for kind, count in [('forecasts', 24), ('actuals', 48)]:
            response = client.get(f'/api/decisions/2026-01-01/{kind}')
            assert response.status_code == 200 and len(response.json()['observations']) == count
        assert client.get('/api/decisions/2026-01-01/metrics').status_code == 200


def test_tampered_snapshot_fails_closed(tmp_path):
    shutil.copytree(ROOT / 'data/raw', tmp_path / 'data/raw')
    path = tmp_path / 'data/raw/WINDFOR-2026-01-01.json'
    path.write_bytes(path.read_bytes() + b' ')
    with TestClient(create_app(Settings(data_root=tmp_path))) as client:
        assert client.get('/api/metrics').status_code == 503
