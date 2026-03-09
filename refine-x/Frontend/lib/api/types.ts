/* ─── TypeScript interfaces mirroring backend Pydantic schemas ──────────── */

/* ── Auth ─────────────────────────────────────────────────────────────────── */

export interface UserResponse {
  id: number;
  name: string | null;
  email: string;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

/* ── Upload / Jobs ────────────────────────────────────────────────────────── */

export type JobStatus =
  | "pending"
  | "processing"
  | "awaiting_review"
  | "completed"
  | "failed";

export interface ColumnRelevanceColumn {
  name: string;
  recommendation: "keep" | "remove";
  reason: string;
}

export interface ColumnRelevanceResult {
  overall_verdict: "useful" | "not_useful";
  reason: string;
  columns: ColumnRelevanceColumn[];
}

export interface UploadJobResponse {
  id: number;
  filename: string;
  file_size: number;
  file_type: string;
  status: JobStatus;
  quality_score: number | null;
  row_count: number | null;
  column_count: number | null;
  column_relevance_result: ColumnRelevanceResult | null;
  confirmed_columns: string[] | null;
  created_at: string;
  processed_at: string | null;
}

export interface UploadJobListResponse {
  id: number;
  filename: string;
  status: JobStatus;
  quality_score: number | null;
  created_at: string;
}

export interface JobStatusResponse {
  job_id: number;
  status: JobStatus;
  progress: number | null;
  quality_score: number | null;
  row_count: number | null;
  error_message: string | null;
  column_relevance_result: ColumnRelevanceResult | null;
}

/* ── Cleaning ─────────────────────────────────────────────────────────────── */

export interface ColumnMeta {
  dtype: string;
  null_count: number;
  unique_count: number;
  sample: string[];
  [key: string]: unknown;
}

export interface CleaningSummaryResponse {
  job_id: number;
  row_count_original: number | null;
  row_count_cleaned: number | null;
  duplicates_removed: number;
  columns_renamed: number;
  columns_dropped: number;
  dates_converted: number;
  ages_bucketed: number;
  missing_filled: number;
  outliers_flagged: number;
  quality_score: number | null;
  column_metadata: Record<string, ColumnMeta> | null;
  created_at: string | null;
}

export interface AuditLogEntry {
  id: number;
  job_id: number;
  row_index: number | null;
  column_name: string | null;
  action: string;
  original_value: string | null;
  new_value: string | null;
  reason: string;
  formula_id: string | null;
  was_auto_applied: boolean | null;
  timestamp: string;
}

export interface MissingFieldsResponse {
  job_id: number;
  missing: Record<string, { count: number; percentage: number }>;
}

export interface OutlierEntry {
  row_index: number;
  column: string;
  value: unknown;
  expected_range: string;
}

export interface OutliersResponse {
  job_id: number;
  outliers: OutlierEntry[];
}

/* ── AI Analysis ──────────────────────────────────────────────────────────── */

export interface UnnecessaryColumn {
  column: string;
  reason: string;
  impact_if_removed: string;
}

export interface AnalyzedColumn {
  column: string;
  decision: 'keep' | 'drop';
  what_it_measures: string;
  why: string;
  analytical_use: string | null;
  warning: string | null;
}

export interface HeaderAnalysisResponse {
  job_id: number;
  columns: AnalyzedColumn[];
  unnecessary_columns: UnnecessaryColumn[];
  essential_columns: string[];
  dataset_summary: string;
}

export interface SuggestedAnalysis {
  name: string;
  description: string;
  why: string;
  columns_needed: string[];
  formula_type: string;
  example: string;
  auto_select: boolean;
}

export interface RecommendedViz {
  chart_type: string;
  x_column: string;
  y_column: string;
  reason: string;
  chart_type_reason: string;
  group_by: string | null;
}

export interface FormulaSuggestionsResponse {
  job_id: number;
  suggested_analyses: SuggestedAnalysis[];
  recommended_visualizations: RecommendedViz[];
}

/* ── Charts ────────────────────────────────────────────────────────────────── */

export interface GoalResponse {
  id: number;
  job_id: number;
  goal_text: string;
  goal_category: string;
}

export interface RecommendationItem {
  x_col: string;
  y_col: string | null;
  chart_type: string;
  relevance_score: number;
  reasoning: string;
  group_by: string | null;
}

export interface ChartConfig {
  xLabel?: string;
  yLabel?: string;
  xDomain?: [number, number] | null;
  yDomain?: [number, number] | null;
  grouped?: boolean;
  series_keys?: string[] | null;
  group_by?: string | null;
  note?: string | null;
  data_key?: string;
  x_data_key?: string;
  y_unit?: 'currency' | 'percent' | 'count' | 'plain';
  layout?: string | null;
  [key: string]: unknown;
}

export interface ChartResponse {
  id: number;
  job_id: number;
  chart_type: string;
  x_header: string;
  y_header: string | null;
  title: string;
  data: unknown[];
  config: ChartConfig | null;
  reason: string | null;
  is_recommended: boolean;
}

export interface ChartListItem {
  id: number;
  job_id: number;
  chart_type: string;
  x_header: string;
  y_header: string | null;
  title: string;
  reason: string | null;
  is_recommended: boolean;
}

/* ── Insights & Annotations ───────────────────────────────────────────────── */

export interface InsightResponse {
  id: number;
  chart_id: number | null;
  job_id: number;
  content: string;
  confidence: string;
  confidence_score: number;
  recommendations: { action: string; reasoning: string }[] | null;
  is_ai_generated: boolean | null;
  model_name: string | null;
}

export interface AnnotationResponse {
  id: number;
  chart_id: number;
  user_id: number;
  data_point_index: number;
  text: string;
}

/* ── Comparison ───────────────────────────────────────────────────────────── */

export interface ComparisonResponse {
  id: number;
  status: string;
  header_mapping: Record<string, string> | null;
  deltas: unknown[] | null;
  significant_changes: unknown[] | null;
  ai_insight: string | null;
}
