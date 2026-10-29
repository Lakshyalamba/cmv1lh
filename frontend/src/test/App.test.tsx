import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import App from '../App';
import samples from './real-api-responses.json';
import { get, fetchDay } from '../api';
import { mw, timeLabel } from '../format';

// Charts are rendered in full by the real-browser integration suite.
vi.mock('../Charts', () => ({
  GenerationChart: ({ rows }: { rows: { forecast_mw: number | null }[] }) => <div data-testid="chart-forecast">{rows[1]?.forecast_mw === null ? 'Half-hour forecast stays null' : 'Unexpected value'}</div>,
  ErrorChart: () => <div>Signed error chart</div>,
}));
const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value));
function mockApi(change?: (path: string, body: any) => any) {
  const fetchMock = vi.fn(async (input: string) => {
    const path = input.replace(/^.*\/api/, '/api').split('?')[0];
    const entry = samples[path as keyof typeof samples];
    if (!entry) return new Response(JSON.stringify({ error: { message: 'Unexpected date' } }), { status: 404 });
    let body: any = clone(entry.body);
    if (change) body = change(path, body);
    return new Response(JSON.stringify(body), { status: 200 });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

describe('dashboard with recorded real API responses', () => {
  it('displays backend metrics, context, chart gaps and real observations', async () => {
    const fetch = mockApi();
    render(<App/>);
    expect(screen.getByRole('status', { name: 'Loading dashboard' })).toBeInTheDocument();
    await screen.findByTestId('metric-mae');
    expect(screen.getByTestId('metric-mae')).toHaveTextContent('3,070.4 MW');
    expect(screen.getByTestId('metric-rmse')).toHaveTextContent('3,139.3 MW');
    expect(screen.getByTestId('metric-bias')).toHaveTextContent('+3,070.4 MW');
    expect(screen.getByTestId('metric-count')).toHaveTextContent('24 / 24');
    expect(screen.getByTestId('chart-forecast')).toHaveTextContent('Half-hour forecast stays null');
    expect(screen.getByText('Wind was overforecast on average')).toBeInTheDocument();
    expect(screen.getByText(/Different resolutions/)).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: 'Decision date' })).toHaveValue('2026-01-01');
    expect(screen.getAllByRole('option')).toHaveLength(31);
    fireEvent.click(screen.getByRole('button', { name: 'View observations +' }));
    expect(screen.getByRole('table')).toHaveTextContent('18,781');
    expect(screen.getByRole('table')).toHaveTextContent('structural forecast gap');
    expect(fetch).toHaveBeenCalledTimes(6);
  });
  it('keeps the loaded analysis when the current date is selected again', async () => {
    mockApi(); render(<App/>);
    await screen.findByTestId('metric-mae');
    fireEvent.change(screen.getByRole('combobox'), { target: { value: '2026-01-01' } });
    expect(screen.getByTestId('metric-mae')).toHaveTextContent('3,070.4 MW');
  });
  it('shows API failure and can retry successfully', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
    render(<App/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Cannot reach the data service');
    expect(screen.queryByTestId('metric-mae')).not.toBeInTheDocument();
    mockApi();
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByTestId('metric-mae')).toHaveTextContent('3,070.4');
  });
  it('supports an empty decision list', async () => {
    mockApi((path, body) => path === '/api/decisions' ? { ...body, decisions: [] } : body);
    render(<App/>);
    expect(await screen.findByText('No decision data available')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeDisabled();
  });
  it('shows null metrics, missing coverage and honest insight with no pairs', async () => {
    mockApi((path, body) => {
      if (path.endsWith('/2026-01-01/metrics')) {
        body.accuracy = { ...body.accuracy, status: 'no_matched_observations', observation_count: 0, mae_mw: null, rmse_mw: null, bias_mw: null };
        body.coverage.missing_hourly_forecasts = 24;
        body.coverage.excluded_hourly_pairs = 24;
      }
      return body;
    });
    render(<App/>);
    expect(await screen.findByText('Not enough matched data')).toBeInTheDocument();
    expect(screen.getByTestId('metric-mae')).toHaveTextContent('— MW');
    expect(screen.getByText(/Accuracy metrics are unavailable, not zero/)).toBeInTheDocument();
    expect(screen.getByText(/24 hourly forecasts/)).toBeInTheDocument();
  });
  it('does not leave old metrics visible after date-change failure', async () => {
    mockApi(); render(<App/>);
    await screen.findByTestId('metric-mae');
    fireEvent.change(screen.getByRole('combobox'), { target: { value: '2026-01-02' } });
    expect(screen.queryByTestId('metric-mae')).not.toBeInTheDocument();
    expect(await screen.findByRole('alert')).toHaveTextContent('Unexpected date');
  });
  it('displays signed negative bias without turning it into an absolute error', async () => {
    mockApi((path, body) => { if (path.endsWith('/2026-01-01/metrics')) body.accuracy.bias_mw = -50; return body; });
    render(<App/>);
    expect(await screen.findByText('Wind was underforecast on average')).toBeInTheDocument();
    expect(screen.getByTestId('metric-bias')).toHaveTextContent('-50 MW');
  });
  it('shows daily endpoint failure without partial or stale analysis', async () => {
    const fetch = mockApi();
    const original = fetch.getMockImplementation()!;
    fetch.mockImplementation(async input => input.includes('/forecasts')
      ? new Response(JSON.stringify({ error: { message: 'Validated data unavailable' } }), { status: 503 }) : original(input));
    render(<App/>);
    expect(await screen.findByRole('alert')).toHaveTextContent('Validated data unavailable');
    expect(screen.queryByTestId('metric-mae')).not.toBeInTheDocument();
  });
});

describe('transport and formatting', () => {
  it('preserves HTTP error status and meaningful message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { message: 'No observations' } }), { status: 404 })));
    await expect(get('/missing')).rejects.toMatchObject({ status: 404, message: 'No observations' });
  });
  it('handles a non-JSON service error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('Bad gateway', { status: 502 })));
    await expect(get('/metrics')).rejects.toMatchObject({ status: 502, message: 'The data service returned HTTP 502.' });
  });
  it('rejects responses for the wrong decision date', async () => {
    mockApi((path, body) => { if (path.endsWith('/forecasts')) body.decision_date = '2026-01-02'; return body; });
    await expect(fetchDay('2026-01-01', '09:20', new AbortController().signal)).rejects.toThrow('inconsistent date or cutoff');
  });
  it('does not coerce missing values to zero and formats GMT explicitly', () => {
    expect(mw(null)).toBe('—'); expect(mw(0)).toBe('0'); expect(mw(12, true)).toBe('+12');
    expect(timeLabel('2026-01-02T00:00:00Z')).toBe('00:00');
  });
  it('aborts pending requests when the caller cancels', async () => {
    const controller = new AbortController();
    vi.stubGlobal('fetch', vi.fn((_path, options: RequestInit) => new Promise((_resolve, reject) => {
      options.signal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
    })));
    const request = get('/metrics', controller.signal);
    controller.abort();
    await expect(request).rejects.toHaveProperty('name', 'AbortError');
  });
});
