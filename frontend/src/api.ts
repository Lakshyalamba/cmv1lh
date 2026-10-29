import type { ActualResponse, ComparisonResponse, DayData, DecisionsResponse, ForecastResponse, MetricsResponse } from './types';
const base = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); this.name = 'ApiError'; }
}
export async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener('abort', abort, { once: true });
  const timer = setTimeout(abort, 20_000);
  try {
    const response = await fetch(`${base}/api${path}`, { signal: controller.signal, headers: { Accept: 'application/json' } });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      throw new ApiError(response.status, body?.error?.message ?? `The data service returned HTTP ${response.status}.`);
    }
    return await response.json() as T;
  } catch (error) {
    if (signal?.aborted) throw error;
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, controller.signal.aborted
      ? 'The data service took too long to respond. Please try again.'
      : 'Cannot reach the data service. Check that the backend is running, then try again.');
  } finally { clearTimeout(timer); signal?.removeEventListener('abort', abort); }
}
export const fetchOverview = (signal: AbortSignal) => Promise.all([
  get<DecisionsResponse>('/decisions', signal), get<MetricsResponse>('/metrics', signal),
]);
export async function fetchDay(date: string, cutoff: string, signal: AbortSignal): Promise<DayData> {
  const query = `?cutoff_local=${encodeURIComponent(cutoff)}`;
  const [forecasts, actuals, comparisons, metrics] = await Promise.all([
    get<ForecastResponse>(`/decisions/${date}/forecasts${query}`, signal),
    get<ActualResponse>(`/decisions/${date}/actuals${query}`, signal),
    get<ComparisonResponse>(`/decisions/${date}/comparisons${query}`, signal),
    get<MetricsResponse>(`/decisions/${date}/metrics${query}`, signal),
  ]);
  // Reject a mismatched response rather than mix data from different dates/cutoffs.
  if ([forecasts, actuals, comparisons].some(r => r.decision_date !== date || r.cutoff_local !== cutoff)
      || metrics.start_decision_date !== date || metrics.end_decision_date !== date || metrics.cutoff_local !== cutoff) {
    throw new ApiError(0, 'The data service returned an inconsistent date or cutoff. Please reload.');
  }
  return { forecasts, actuals, comparisons, metrics };
}
