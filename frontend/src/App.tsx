import { useState } from 'react';
import { ErrorChart, GenerationChart } from './Charts';
import { dateLabel, mw, publicationLabel, timeLabel } from './format';
import type { DayData, MetricsResponse } from './types';
import { useDashboard } from './useDashboard';

function Mark() {
  return <svg viewBox="0 0 32 32" width="30" height="30" fill="none" aria-hidden="true"><path d="M16 27V15m0 0L8 5m8 10 11-3m-11 3L8 23" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/><circle cx="16" cy="15" r="3" fill="currentColor"/></svg>;
}
function Skeleton() {
  return <div role="status" aria-label="Loading dashboard" className="space-y-5"><span className="sr-only">Loading dashboard…</span><div className="grid grid-cols-2 gap-4 lg:grid-cols-4">{[1, 2, 3, 4].map(n => <div key={n} className="skeleton h-32" />)}</div><div className="skeleton h-96"/><div className="skeleton h-56"/></div>;
}
function Problem({ message, retry }: { message: string; retry: () => void }) {
  return <section role="alert" className="state-panel"><span className="eyebrow">Data service unavailable</span><h2>We couldn’t load this analysis.</h2><p>{message}</p><button className="button" onClick={retry}>Try again</button><p className="text-sm">No example data is shown in place of Elexon observations.</p></section>;
}
function Metrics({ metrics }: { metrics: MetricsResponse }) {
  const a = metrics.accuracy;
  return <section aria-label="Forecast accuracy metrics" className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
    {[
      { label: 'Mean absolute error', value: a.mae_mw, note: 'Average size of the forecast error.', tag: 'MAE' },
      { label: 'Root mean squared error', value: a.rmse_mw, note: 'Gives more weight to larger misses.', tag: 'RMSE' },
      { label: 'Signed forecast bias', value: a.bias_mw, note: 'Positive = overforecast; negative = underforecast.', tag: 'BIAS' },
    ].map(m => <article key={m.tag} className="metric"><div className="flex items-center justify-between gap-2"><h3>{m.label}</h3><span className="metric-tag">{m.tag}</span></div><p className="metric-value" data-testid={`metric-${m.tag.toLowerCase()}`}>{mw(m.value, m.tag === 'BIAS')} <span>MW</span></p><p className="metric-note">{m.note}</p></article>)}
    <article className="metric"><div className="flex items-center justify-between"><h3>Matched observations</h3><span className="metric-tag">PAIRS</span></div><p className="metric-value" data-testid="metric-count">{a.observation_count}<span> / {metrics.coverage.expected_hourly_targets}</span></p><p className="metric-note">Native hourly targets with a matching actual.</p></article>
  </section>;
}
function DayDashboard({ data, month }: { data: DayData; month: MetricsResponse }) {
  const { comparisons: c, forecasts: f, actuals: a, metrics: m } = data;
  const bias = m.accuracy.bias_mw;
  const publications = [...new Set(f.observations.map(p => p.publish_time).filter((p): p is string => p !== null))].sort();
  const [showTable, setShowTable] = useState(false);
  return <>
    <section className="decision-strip" aria-label="Selected decision context">
      <div><span className="eyebrow">Procurement decision</span><strong>{dateLabel(c.decision_date)}</strong><span>Information strictly before {c.cutoff_local} GMT</span></div>
      <div><span className="eyebrow">Delivery day</span><strong>{dateLabel(c.delivery_date)}</strong><span>00:00–23:30 · Europe/London (GMT)</span></div>
      <div><span className="eyebrow">Forecast coverage</span><strong>{m.coverage.forecast_observations} / {m.coverage.expected_hourly_targets} hourly targets</strong><span>{m.coverage.actual_observations} / {m.coverage.expected_half_hours} half-hour actuals</span></div>
      <div><span className="eyebrow">Forecast published</span><strong>{publications.length === 1 ? `${publicationLabel(publications[0])} GMT` : `${publications.length} publication vintages`}</strong><span>WINDFOR · selected before cutoff</span></div>
    </section>
    <div className="section-label"><h2>How accurate was this decision’s forecast?</h2><span className="badge retrospective">Retrospective evaluation</span></div>
    <Metrics metrics={m}/>
    {m.accuracy.status === 'no_matched_observations' && <div role="status" className="notice">No matched observations. Accuracy metrics are unavailable, not zero.</div>}
    {(m.coverage.missing_hourly_forecasts > 0 || m.coverage.missing_half_hour_actuals > 0) && <div className="notice" role="status">Partial data: {m.coverage.missing_hourly_forecasts} hourly forecasts and {m.coverage.missing_half_hour_actuals} half-hour actuals are missing. {m.coverage.excluded_hourly_pairs} hourly pairs are excluded from accuracy metrics.</div>}
    <section className="panel generation-panel" aria-labelledby="generation-title">
      <div className="panel-heading"><div><span className="eyebrow">Delivery-day profile</span><h2 id="generation-title">Forecast vs actual generation</h2><p>{dateLabel(c.delivery_date)} · all times Europe/London (GMT)</p></div><span className="badge available">● Forecast available at decision time</span></div>
      <GenerationChart rows={c.observations}/>
      <div className="chart-footnote"><span aria-hidden="true">ⓘ</span><p><strong>Different resolutions.</strong> WINDFOR forecasts are hourly points; FUELHH actuals are half-hour averages. Forecast points are not connected across unavailable half-hours. Equal-time comparisons are a proxy, not full half-hour forecast accuracy.</p></div>
    </section>
    <div className="analysis-grid">
      <section className="panel" aria-labelledby="error-title"><div className="panel-heading"><div><span className="eyebrow">Where the forecast missed</span><h2 id="error-title">Forecast error through the day</h2><p>Error = Forecast − Actual · MW · GMT</p></div></div><div className="error-legend"><span><i className="swatch amber"/> Overforecast</span><span><i className="swatch teal"/> Underforecast</span></div><ErrorChart rows={c.observations}/><p className="panel-caption">Only matched hourly targets have an error value. Blank half-hours are not zero errors.</p></section>
      <aside className="insight-panel" aria-labelledby="insight-title"><span className="eyebrow">Decision perspective</span><h2 id="insight-title">What this tells you</h2>
        <div className="insight-callout"><span className="insight-symbol" aria-hidden="true">{bias === null ? '—' : bias > 0 ? '↗' : bias < 0 ? '↘' : '≈'}</span><h3>{bias === null ? 'Not enough matched data' : bias > 0 ? 'Wind was overforecast on average' : bias < 0 ? 'Wind was underforecast on average' : 'No net forecast bias'}</h3></div>
        <p>{bias === null ? 'There are no matched forecast and actual observations to assess this decision.' : <>The signed average difference was <strong>{mw(bias, true)} MW</strong> across <strong>{m.accuracy.observation_count}</strong> matched targets. Individual errors can vary through the day.</>}</p>
        <p>Overestimating wind could leave a supply shortfall; underestimating it could lead to excess purchases, all else equal. Historical errors help frame uncertainty, but do not guarantee future outcomes.</p>
        <div className="insight-divider"/><h3>Keep the wider picture</h3><p>Wind data alone cannot determine how much electricity to buy. Customer demand, other supply commitments and market conditions are also needed.</p>
        <span className="insight-bottom">Historical evidence · not a purchase recommendation</span>
      </aside>
    </div>
    <section className="panel source-panel"><div className="panel-heading"><div><span className="eyebrow">Trace the evidence</span><h2>Sources & observation detail</h2><p>{f.dataset} forecasts · {a.dataset} WIND actuals · Elexon historical snapshot</p></div><button className="text-button" aria-expanded={showTable} aria-controls="observation-detail" onClick={() => setShowTable(v => !v)}>{showTable ? 'Hide observations −' : 'View observations +'}</button></div>
      <div className="source-grid"><div><h3>Known before procurement</h3><p>Only forecasts published strictly before {c.cutoff_local} GMT on {dateLabel(c.decision_date)} are selected. Publication time is a proxy for availability; client receipt delays and late backfills are unknown.</p><p className="publication-list">Selected publications: {publications.length ? publications.map(p => `${publicationLabel(p)} GMT`).join(' · ') : 'none available'}.</p></div><div><h3>Measured after delivery</h3><p>Actual generation uses the latest publication in the extracted snapshot. Actuals and error statistics are retrospective and were not available at procurement time.</p></div></div>
      {showTable && <div id="observation-detail" className="table-scroll" tabIndex={0} aria-label="Scrollable observation table"><table><caption>Delivery {dateLabel(c.delivery_date)} · all times GMT · generation and errors in MW</caption><thead><tr><th scope="col">Time</th><th scope="col">Forecast MW</th><th scope="col">Actual MW</th><th scope="col">Error MW</th><th scope="col">Forecast published</th><th scope="col">Status</th></tr></thead><tbody>{c.observations.map(r => <tr key={r.start_time}><th scope="row">{timeLabel(r.start_time)}</th><td>{mw(r.forecast_mw)}</td><td>{mw(r.actual_mw)}</td><td>{mw(r.error_mw, true)}</td><td>{r.forecast_publish_time ? `${publicationLabel(r.forecast_publish_time)} GMT` : '—'}</td><td>{r.status.replaceAll('_', ' ')}</td></tr>)}</tbody></table></div>}
    </section>
    <section className="month-reference" aria-label="January retrospective reference"><div><span className="eyebrow">January reference</span><p>All 31 decision dates · same {month.cutoff_local} GMT cutoff</p></div><div><strong>{mw(month.accuracy.mae_mw)} MW</strong><span>Pooled MAE</span></div><div><strong>{mw(month.accuracy.bias_mw, true)} MW</strong><span>Pooled signed bias</span></div><div><strong>{month.accuracy.observation_count}</strong><span>Matched observations</span></div></section>
  </>;
}
export default function App() {
  const { overview, day, selected, select, retry } = useDashboard();
  const dates = overview.status === 'ready' ? overview.data.dates.decisions : [];
  const available = dates.filter(d => d.available);
  const index = available.findIndex(d => d.decision_date === selected);
  return <><a className="skip-link" href="#analysis">Skip to analysis</a><header className="masthead"><div className="masthead-inner"><a href="#" className="brand" aria-label="Wind intelligence home"><span className="brand-icon"><Mark/></span><span>Wind intelligence<small>DAY-AHEAD ANALYTICS</small></span></a><div className="masthead-context"><span className="status-dot"/> Great Britain<span className="masthead-divider"/>January 2026</div></div></header>
    <main id="analysis" className="page-shell"><div className="page-intro"><div><div className="eyebrow intro-eyebrow">Elexon data / procurement analysis</div><h1>Wind forecast analysis</h1><p>Explore what was known before procurement — and what happened after delivery.</p></div><span className="snapshot-label">Historical snapshot</span></div>
      <section className="toolbar" aria-label="Analysis controls"><div><label htmlFor="decision-date">Decision date</label><div className="date-controls"><button aria-label="Previous decision date" disabled={index <= 0} onClick={() => select(available[index - 1].decision_date)}>←</button><select id="decision-date" value={selected} disabled={!dates.length} onChange={e => select(e.target.value)}>{!selected && <option value="">{overview.status === 'loading' ? 'Loading dates…' : 'No available dates'}</option>}{dates.map(d => <option key={d.decision_date} value={d.decision_date} disabled={!d.available}>{dateLabel(d.decision_date)}{!d.available ? ' · unavailable' : ''}</option>)}</select><button aria-label="Next decision date" disabled={index < 0 || index >= available.length - 1} onClick={() => select(available[index + 1].decision_date)}>→</button></div></div><div className="cutoff-context"><span className="eyebrow">Assumed procurement cutoff</span><strong>{overview.status === 'ready' ? overview.data.dates.cutoff_local : '—'} <span>Europe/London · GMT in January</span></strong><p>Latest publication strictly before cutoff. Delivery is the following day.</p></div></section>
      {overview.status === 'loading' ? <Skeleton/> : overview.status === 'error' ? <Problem message={overview.message} retry={retry}/> : !selected ? <section className="state-panel" role="status"><h2>No decision data available</h2><p>The service returned no available decision dates. No substitute data is displayed.</p><button className="button" onClick={retry}>Reload dates</button></section> : day.status === 'loading' || (day.status === 'ready' && day.data.comparisons.decision_date !== selected) ? <Skeleton/> : day.status === 'error' ? <Problem message={day.message} retry={retry}/> : <DayDashboard key={selected} data={day.data} month={overview.data.month}/>}
      <footer><span>Wind intelligence · Gridbricks internship project</span><a href="https://www.elexon.co.uk/bsc/data/balancing-mechanism-reporting-agent/copyright-licence-bmrs-data/" target="_blank" rel="noreferrer">Contains BMRS data © Elexon Limited copyright and database right 2026.</a></footer>
    </main></>;
}
