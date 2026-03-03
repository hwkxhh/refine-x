import { api } from "./client";
import type { InsightResponse, AnnotationResponse } from "./types";

/** AI generates a text insight for a chart. */
export function generateInsight(
  chartId: number,
): Promise<InsightResponse> {
  return api.post(`/charts/${chartId}/insights`);
}

/** List all insights for a job. */
export function listInsights(jobId: number): Promise<InsightResponse[]> {
  return api.get(`/jobs/${jobId}/insights`);
}

/** Get a single insight. */
export function getInsight(insightId: number): Promise<InsightResponse> {
  return api.get(`/insights/${insightId}`);
}

/** Add an annotation to a chart data point. */
export function addAnnotation(
  jobId: number,
  chartId: number,
  dataPointIndex: number,
  text: string,
): Promise<AnnotationResponse> {
  return api.post(`/jobs/${jobId}/charts/${chartId}/annotations`, {
    data_point_index: dataPointIndex,
    text,
  });
}

/** List annotations on a chart. */
export function listAnnotations(
  jobId: number,
  chartId: number,
): Promise<AnnotationResponse[]> {
  return api.get(`/jobs/${jobId}/charts/${chartId}/annotations`);
}

/** Delete own annotation. */
export function deleteAnnotation(annotationId: number): Promise<void> {
  return api.delete(`/annotations/${annotationId}`);
}
