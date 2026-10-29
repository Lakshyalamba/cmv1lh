"""Run: python -m pipeline.fetch. Raw responses are immutable unless --refresh."""
import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/'


def request_json(url, attempts=4):
    for attempt in range(attempts):
        try:
            with urlopen(Request(url, headers={'Accept': 'application/json'}), timeout=60) as response:
                body = response.read()
            rows = json.loads(body)
            if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
                raise ValueError('Expected a JSON array of records')
            return body, rows
        except (HTTPError, URLError, TimeoutError) as exc:
            if isinstance(exc, HTTPError) and exc.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == attempts - 1:
                raise
            retry_after = exc.headers.get('Retry-After') if isinstance(exc, HTTPError) else None
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
            time.sleep(min(delay, 120))


def fetch(refresh=False):
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    # Forecast publication windows: seven-day warm-up plus all January decisions.
    for dataset, first, last in [('WINDFOR', date(2025, 12, 25), date(2026, 1, 31)),
                                 ('FUELHH', date(2026, 1, 2), date(2026, 2, 1))]:
        day = first
        while day <= last:
            if dataset == 'WINDFOR':
                params = {'publishDateTimeFrom': f'{day}T00:00:00Z',
                          'publishDateTimeTo': f'{day + timedelta(days=1)}T00:00:00Z'}
            else:
                params = {'settlementDateFrom': str(day), 'settlementDateTo': str(day), 'fuelType': 'WIND'}
            path = raw / f'{dataset}-{day}.json'
            url = BASE + dataset + '/stream?' + urlencode(params)
            if refresh or not path.exists():
                body, rows = request_json(url)
                path.write_bytes(body)
                path.with_suffix('.meta.json').write_text(json.dumps({
                    'url': url, 'retrievedAt': datetime.now(timezone.utc).isoformat(),
                    'sha256': hashlib.sha256(body).hexdigest(), 'records': len(rows)
                }, indent=2) + '\n')
                print(path.name, len(rows), flush=True)
                time.sleep(0.15)
            day += timedelta(days=1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true')
    fetch(parser.parse_args().refresh)
