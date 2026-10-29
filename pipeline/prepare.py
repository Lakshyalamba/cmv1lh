"""Validate native records and select forecasts without future information."""
from datetime import date, datetime, time, timedelta
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
from .fetch import ROOT


def normalize(records, dataset):
    if not records:
        raise ValueError(f'{dataset}: no source records')
    frame = pd.DataFrame(records)
    required = {'dataset', 'startTime', 'publishTime', 'generation'}
    if not required.issubset(frame.columns) or not frame.dataset.eq(dataset).all():
        raise ValueError(f'{dataset}: wrong dataset or missing fields')
    if dataset == 'FUELHH':
        if 'fuelType' not in frame or not frame.fuelType.eq('WIND').all():
            raise ValueError('Only WIND actuals are allowed')
    for column in ['startTime', 'publishTime']:
        # Require explicit offset: never silently interpret naive dates as UTC.
        if not frame[column].map(lambda v: isinstance(v, str) and
                                 (v.endswith('Z') or '+' in v[10:] or '-' in v[10:])).all():
            raise ValueError(f'{column}: missing timezone')
        frame[column] = pd.to_datetime(frame[column], utc=True, errors='raise', format='ISO8601')
    frame['generation'] = pd.to_numeric(frame.generation, errors='raise')
    if not (np.isfinite(frame.generation) & frame.generation.ge(0)).all():
        raise ValueError('Missing, negative or non-finite generation')
    if not frame.startTime.eq(frame.startTime.dt.floor('30min')).all():
        raise ValueError('Target is not on a settlement boundary')
    original = len(frame)
    frame = frame.drop_duplicates()
    key = ['startTime', 'publishTime']
    if frame.duplicated(key).any():
        raise ValueError(f'{dataset}: conflicting records for target/publication')
    stats = {'raw_records': original, 'exact_duplicates_removed': original - len(frame),
             'unique_records': len(frame), 'target_count': frame.startTime.nunique(),
             'publication_count': frame.publishTime.nunique(),
             'generation_min_mw': float(frame.generation.min()),
             'generation_max_mw': float(frame.generation.max()),
             'target_min': str(frame.startTime.min()), 'target_max': str(frame.startTime.max()),
             'targets_with_revisions': int(frame.groupby('startTime').size().gt(1).sum()),
             'target_minutes': sorted(frame.startTime.dt.minute.unique().tolist())}
    return frame.sort_values(key), stats


def cutoff(day, cutoff_time=time(9, 20)):
    return pd.Timestamp(datetime.combine(day, cutoff_time, ZoneInfo('Europe/London'))).tz_convert('UTC')


def align(forecasts, actuals, first=date(2026, 1, 1), last=date(2026, 1, 31), cutoff_time=time(9, 20)):
    output = []
    day = first
    # Actuals use most recently published historical outturn, never to select forecasts.
    latest_actuals = actuals.sort_values('publishTime').drop_duplicates('startTime', keep='last')
    while day <= last:
        start = pd.Timestamp(day + timedelta(days=1), tz='Europe/London').tz_convert('UTC')
        end = pd.Timestamp(day + timedelta(days=2), tz='Europe/London').tz_convert('UTC')
        grid = pd.DataFrame({'startTime': pd.date_range(start, end, freq='30min', inclusive='left')})
        eligible = forecasts[(forecasts.publishTime < cutoff(day, cutoff_time)) &
                             (forecasts.startTime >= start) & (forecasts.startTime < end)]
        selected = eligible.sort_values('publishTime').drop_duplicates('startTime', keep='last')
        joined = grid.merge(selected[['startTime', 'publishTime', 'generation']], on='startTime', how='left')
        joined = joined.rename(columns={'publishTime': 'forecastPublishTime', 'generation': 'forecastMw'})
        joined = joined.merge(latest_actuals[['startTime', 'publishTime', 'generation']], on='startTime', how='left')
        joined = joined.rename(columns={'publishTime': 'actualPublishTime', 'generation': 'actualMw'})
        joined['decisionDate'] = str(day)
        joined['decisionCutoff'] = cutoff(day, cutoff_time)
        joined['errorMw'] = joined.forecastMw - joined.actualMw
        output.append(joined)
        day += timedelta(days=1)
    return pd.concat(output, ignore_index=True)


def load_sources(root=ROOT):
    """Read and validate the complete checksum-verified Phase 1 extraction."""
    root = Path(root)
    frames, report = {}, {}
    for dataset, first, last in [('WINDFOR', date(2025, 12, 25), date(2026, 1, 31)),
                                 ('FUELHH', date(2026, 1, 2), date(2026, 2, 1))]:
        day = first
        while day <= last:
            path = root / 'data/raw' / f'{dataset}-{day}.json'
            if not path.exists() or not path.with_suffix('.meta.json').exists():
                raise ValueError(f'Incomplete extraction: {path.name}; run pipeline.fetch')
            day += timedelta(days=1)
    for dataset in ['WINDFOR', 'FUELHH']:
        records = []
        for path in sorted((root / 'data/raw').glob(f'{dataset}-*.json')):
            if path.name.endswith('.meta.json'):
                continue
            body = path.read_bytes()
            meta = json.loads(path.with_suffix('.meta.json').read_text())
            if hashlib.sha256(body).hexdigest() != meta['sha256']:
                raise ValueError(f'Checksum mismatch: {path}')
            records.extend(json.loads(body))
        frames[dataset], report[dataset] = normalize(records, dataset)
    return frames, report


def main():
    frames, report = load_sources(ROOT)
    result = align(frames['WINDFOR'], frames['FUELHH'])
    report['alignment'] = {'expected_half_hours': len(result),
        'forecast_present': int(result.forecastMw.notna().sum()),
        'actual_present': int(result.actualMw.notna().sum()),
        'matched_native_targets': int(result.errorMw.notna().sum()),
        'future_forecasts_selected': int((result.forecastPublishTime >= result.decisionCutoff).sum()),
        'forecast_absent_by_decision': result.groupby('decisionDate').forecastMw.apply(lambda s: int(s.isna().sum())).to_dict()}
    out = ROOT / 'data/processed'
    out.mkdir(parents=True, exist_ok=True)
    result.to_csv(out / 'aligned.csv', index=False)
    for name, frame in frames.items():
        frame.to_csv(out / f'{name.lower()}.csv', index=False)
    (ROOT / 'docs/inspection.json').write_text(json.dumps(report, indent=2, default=int) + '\n')
    print(json.dumps(report, indent=2, default=int))


if __name__ == '__main__':
    main()
