from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from backend.config import Settings
from backend.main import create_app
from backend.run import main
from pipeline.fetch import ROOT


def static_build(tmp_path):
    (tmp_path / 'assets').mkdir()
    (tmp_path / 'index.html').write_text('<html><h1>Static build fixture</h1></html>')
    (tmp_path / 'assets/app.js').write_text('console.log("test");')
    return tmp_path


def test_static_and_api_share_origin_with_health(tmp_path):
    with TestClient(create_app(Settings(static_dir=static_build(tmp_path)))) as client:
        assert client.get('/health/live').json() == {'status': 'live'}
        assert client.get('/health/ready').json() == {'status': 'ready'}
        assert client.get('/').headers['content-type'].startswith('text/html')
        assert client.get('/').headers['cache-control'] == 'no-cache'
        assert client.get('/assets/app.js').status_code == 200
        assert client.get('/api/decisions').status_code == 200
        assert client.get('/api/typo').status_code == 404
        assert client.get('/assets/../../backend/main.py').status_code == 404
        # No wildcard CORS exposure; same-origin requests need no CORS middleware.
        assert 'access-control-allow-origin' not in client.get('/api/metrics', headers={'Origin': 'https://unrelated.example'}).headers


def test_health_distinguishes_missing_data_and_missing_frontend(tmp_path):
    with TestClient(create_app(Settings(data_root=tmp_path))) as client:
        assert client.get('/health/live').status_code == 200
        assert client.get('/health/ready').status_code == 503
        assert client.get('/api/metrics').status_code == 503
    with TestClient(create_app(Settings(static_dir=tmp_path))) as client:
        assert client.get('/health/ready').status_code == 503
        assert client.get('/').json()['error']['code'] == 'frontend_unavailable'
        assert client.get('/assets/app.js').status_code == 404
        assert client.get('/api/metrics').status_code == 200


def test_unhandled_errors_are_logged_without_leaking_details():
    app = create_app()
    @app.get('/test-failure')
    def failure():
        raise RuntimeError('secret internal diagnostic')
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get('/test-failure')
        assert response.status_code == 500
        assert response.json()['error']['code'] == 'internal_error'
        assert 'secret' not in response.text


def test_entrypoint_honors_platform_port_and_shutdown(monkeypatch):
    monkeypatch.setenv('PORT', '8765')
    monkeypatch.setenv('LOG_LEVEL', 'warning')
    with patch('backend.run.uvicorn.run') as run:
        main()
        assert run.call_args.kwargs['port'] == 8765
        assert run.call_args.kwargs['host'] == '0.0.0.0'
        assert run.call_args.kwargs['timeout_graceful_shutdown'] == 20
    monkeypatch.setenv('PORT', '0')
    with pytest.raises(ValueError):
        main()


def test_deployment_snapshot_is_valid_and_reproducible(tmp_path):
    import gzip, hashlib, io, tarfile
    from scripts.package_data import package
    snapshot = ROOT / 'data/snapshot.tar.gz'
    digest = (ROOT / 'data/snapshot.sha256').read_text().split()[0]
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == digest
    with tarfile.open(fileobj=io.BytesIO(gzip.decompress(snapshot.read_bytes()))) as archive:
        assert len(archive.getmembers()) == 138
        archive.extractall(tmp_path, filter='data')
    from pipeline.prepare import load_sources
    load_sources(tmp_path)
    package(tmp_path)
    assert (tmp_path / 'data/snapshot.tar.gz').read_bytes() == snapshot.read_bytes()
