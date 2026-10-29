export interface Coverage {
  expected_half_hours: number; expected_hourly_targets: number; forecast_observations: number;
  actual_observations: number; matched_observations: number; missing_hourly_forecasts: number;
  missing_half_hour_actuals: number; structural_half_hour_forecast_gaps: number; excluded_hourly_pairs: number;
}
export interface Context {
  unit: 'MW'; timezone: 'Europe/London'; cutoff_local: string;
  forecast_resolution_minutes: 60; actual_resolution_minutes: 30;
  comparison_basis: string; analysis_mode: 'retrospective_evaluation'; warnings: string[];
}
export interface Decision {
  decision_date: string; delivery_date: string; decision_cutoff_utc: string; available: boolean; coverage: Coverage;
}
export interface DecisionsResponse extends Context { decisions: Decision[] }
export interface DayContext extends Context {
  decision_date: string; delivery_date: string; decision_cutoff_utc: string; coverage: Coverage;
}
export interface Observation { start_time: string; publish_time: string | null; generation_mw: number | null }
export interface ForecastResponse extends DayContext { dataset: 'WINDFOR'; observations: Observation[] }
export interface ActualResponse extends DayContext {
  dataset: 'FUELHH'; fuel_type: 'WIND'; actual_revision_policy: string; observations: Observation[];
}
export interface ComparisonPoint {
  start_time: string; forecast_publish_time: string | null; actual_publish_time: string | null;
  forecast_mw: number | null; actual_mw: number | null; error_mw: number | null;
  status: 'matched' | 'structural_forecast_gap' | 'missing_forecast' | 'missing_actual' | 'missing_both';
}
export interface ComparisonResponse extends DayContext { observations: ComparisonPoint[] }
export interface Accuracy {
  status: 'ok' | 'no_matched_observations'; observation_count: number;
  mae_mw: number | null; rmse_mw: number | null; bias_mw: number | null;
  error_definition: 'forecast_mw - actual_mw';
}
export interface MetricsResponse extends Context {
  start_decision_date: string; end_decision_date: string; coverage: Coverage; accuracy: Accuracy; retrospective_only: true;
}
export interface DayData {
  forecasts: ForecastResponse; actuals: ActualResponse; comparisons: ComparisonResponse; metrics: MetricsResponse;
}
