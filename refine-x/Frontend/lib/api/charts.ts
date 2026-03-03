import { api } from "./client";
import type {
  GoalResponse,
  RecommendationItem,
  ChartResponse,
  ChartListItem,
} from "./types";

/** Set the user's analysis goal for a job. */
export function setGoal(
  jobId: number,
  goalText: string,
  goalCategory = "custom",
): Promise<GoalResponse> {
  return api.post(`/jobs/${jobId}/goal`, {
    goal_text: goalText,
    goal_category: goalCategory,
  });
}

/** Get the goal for a job. */
export function getGoal(jobId: number): Promise<GoalResponse> {
  return api.get(`/jobs/${jobId}/goal`);
}

/** Get AI chart recommendations based on goal + data shape. */
export function getRecommendations(
  jobId: number,
): Promise<RecommendationItem[]> {
  return api.get(`/jobs/${jobId}/recommendations`);
}

/** Generate a chart. */
export function generateChart(
  jobId: number,
  xCol: string,
  yCol?: string,
  isRecommended = false,
): Promise<ChartResponse> {
  return api.post(`/jobs/${jobId}/charts`, {
    x_col: xCol,
    y_col: yCol ?? null,
    is_recommended: isRecommended,
  });
}

/** List all charts for a job. */
export function listCharts(jobId: number): Promise<ChartListItem[]> {
  return api.get(`/jobs/${jobId}/charts`);
}

/** Get a single chart with its full data. */
export function getChart(
  jobId: number,
  chartId: number,
): Promise<ChartResponse> {
  return api.get(`/jobs/${jobId}/charts/${chartId}`);
}

/** Delete a chart. */
export function deleteChart(
  jobId: number,
  chartId: number,
): Promise<void> {
  return api.delete(`/jobs/${jobId}/charts/${chartId}`);
}

/** Generate a correlation heatmap. */
export function getCorrelation(jobId: number): Promise<unknown> {
  return api.get(`/jobs/${jobId}/correlation`);
}
