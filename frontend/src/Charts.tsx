import { Bar, BarChart, CartesianGrid, Cell, ComposedChart, Legend, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { ComparisonPoint } from './types';
import { mw, timeLabel } from './format';

export function GenerationChart({ rows }: { rows: ComparisonPoint[] }) {
  if (!rows.some(r => r.forecast_mw !== null || r.actual_mw !== null)) return <p className="empty-chart">No generation observations for this delivery day.</p>;
  return <div className="chart" role="img" aria-label="Generation comparison: hourly forecast points and half-hour actual generation, in megawatts. Exact values are available in the observation table.">
    <ResponsiveContainer width="100%" height="100%" minWidth={0}>
      <ComposedChart data={rows} margin={{ top: 14, right: 12, bottom: 10, left: 5 }} accessibilityLayer>
        <CartesianGrid stroke="#e5eaec" vertical={false} strokeDasharray="3 4" />
        <XAxis dataKey="start_time" tickFormatter={timeLabel} ticks={rows.filter((_, i) => i % 8 === 0).map(r => r.start_time)} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#647580' }} minTickGap={12} />
        <YAxis tickFormatter={value => Number(value).toLocaleString('en-GB')} width={63} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#647580' }} label={{ value: 'MW', position: 'insideTopLeft', offset: -4, fill: '#647580', fontSize: 11 }} />
        <Tooltip content={({ active, payload }) => {
          const r = payload?.[0]?.payload as ComparisonPoint | undefined;
          return active && r ? <div className="chart-tooltip"><strong>{timeLabel(r.start_time)} GMT · delivery time</strong><p className="text-teal-700">Forecast {mw(r.forecast_mw)} MW</p><p>Actual {mw(r.actual_mw)} MW</p><small>{r.forecast_mw === null ? 'No native forecast at this time' : 'Forecast available before cutoff'}</small></div> : null;
        }} />
        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />
        <Line name="Actual · retrospective" type="linear" dataKey="actual_mw" stroke="#586b9e" strokeWidth={2.2} dot={false} connectNulls={false} isAnimationActive={false} />
        <Line name="Forecast · available at cutoff" type="linear" dataKey="forecast_mw" stroke="#087f72" strokeWidth={2} dot={{ r: 3.5, fill: '#087f72', stroke: '#fff', strokeWidth: 1 }} activeDot={{ r: 5 }} connectNulls={false} isAnimationActive={false} legendType="circle" />
      </ComposedChart>
    </ResponsiveContainer>
  </div>;
}

export function ErrorChart({ rows }: { rows: ComparisonPoint[] }) {
  if (!rows.some(r => r.error_mw !== null)) return <p className="empty-chart">No matched observations to calculate forecast error.</p>;
  return <div className="chart error-chart" role="img" aria-label="Signed forecast error in megawatts. Amber means overforecast; teal means underforecast. Exact values are available in the observation table.">
    <ResponsiveContainer width="100%" height="100%" minWidth={0}>
      <BarChart data={rows} margin={{ top: 12, right: 10, bottom: 4, left: 5 }} accessibilityLayer>
        <CartesianGrid stroke="#e5eaec" vertical={false} strokeDasharray="3 4" />
        <XAxis dataKey="start_time" tickFormatter={timeLabel} ticks={rows.filter((_, i) => i % 8 === 0).map(r => r.start_time)} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#647580' }} />
        <YAxis width={63} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#647580' }} label={{ value: 'MW', position: 'insideTopLeft', offset: -4, fill: '#647580', fontSize: 11 }} />
        <ReferenceLine y={0} stroke="#6c7c83" />
        <Tooltip content={({ active, payload }) => {
          const r = payload?.[0]?.payload as ComparisonPoint | undefined;
          return active && r && r.error_mw !== null ? <div className="chart-tooltip"><strong>{timeLabel(r.start_time)} GMT</strong><p>{mw(r.error_mw, true)} MW</p><small>{r.error_mw > 0 ? 'Overforecast' : r.error_mw < 0 ? 'Underforecast' : 'No error at this timestamp'}</small></div> : null;
        }} />
        <Bar dataKey="error_mw" name="Forecast − actual" radius={[3, 3, 0, 0]} maxBarSize={14} isAnimationActive={false}>
          {rows.map(r => <Cell key={r.start_time} fill={(r.error_mw ?? 0) >= 0 ? '#bd8035' : '#087f72'} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  </div>;
}
