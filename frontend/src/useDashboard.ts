import { useEffect, useState } from 'react';
import { ApiError, fetchDay, fetchOverview } from './api';
import type { DayData, DecisionsResponse, MetricsResponse } from './types';
type Resource<T> = { status: 'loading' } | { status: 'error'; message: string } | { status: 'ready'; data: T };
export function useDashboard() {
  const [revision, setRevision] = useState(0);
  const [selected, setSelected] = useState('');
  const [overview, setOverview] = useState<Resource<{ dates: DecisionsResponse; month: MetricsResponse }>>({ status: 'loading' });
  const [day, setDay] = useState<Resource<DayData>>({ status: 'loading' });
  useEffect(() => {
    const controller = new AbortController();
    setOverview({ status: 'loading' });
    setDay({ status: 'loading' });
    fetchOverview(controller.signal).then(([dates, month]) => {
      if (controller.signal.aborted) return;
      setOverview({ status: 'ready', data: { dates, month } });
      setSelected(current => dates.decisions.some(d => d.decision_date === current && d.available)
        ? current : dates.decisions.find(d => d.available)?.decision_date ?? '');
    }).catch(error => {
      if (!controller.signal.aborted) setOverview({ status: 'error', message: error instanceof Error ? error.message : 'Unable to load decision dates.' });
    });
    return () => controller.abort();
  }, [revision]);
  useEffect(() => {
    if (overview.status !== 'ready' || !selected) return;
    const controller = new AbortController();
    setDay({ status: 'loading' });
    fetchDay(selected, overview.data.dates.cutoff_local, controller.signal).then(data => {
      if (!controller.signal.aborted) setDay({ status: 'ready', data });
    }).catch(error => {
      if (!controller.signal.aborted) setDay({ status: 'error', message: error instanceof ApiError ? error.message : 'Unable to load this decision.' });
    });
    return () => controller.abort();
  }, [selected, overview]);
  return { overview, day, selected, select: (date: string) => { if (date !== selected) { setDay({ status: 'loading' }); setSelected(date); } }, retry: () => setRevision(r => r + 1) };
}
