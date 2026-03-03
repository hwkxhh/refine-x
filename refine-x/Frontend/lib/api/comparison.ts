import { api } from "./client";
import type { ComparisonResponse } from "./types";

/** Create comparison between two jobs (fuzzy header match). */
export function createComparison(
  jobId1: number,
  jobId2: number,
): Promise<ComparisonResponse> {
  return api.post("/compare", { job_id_1: jobId1, job_id_2: jobId2 });
}

/** Confirm column mapping → compute deltas. */
export function confirmMapping(
  compId: number,
  mapping: Record<string, string>,
): Promise<ComparisonResponse> {
  return api.post(`/compare/${compId}/confirm-mapping`, { mapping });
}

/** Get raw delta values. */
export function getDeltas(compId: number): Promise<ComparisonResponse> {
  return api.get(`/compare/${compId}/deltas`);
}

/** Get significant changes only. */
export function getSignificantChanges(
  compId: number,
): Promise<ComparisonResponse> {
  return api.get(`/compare/${compId}/significant-changes`);
}

/** AI generates narrative insight about the comparison. */
export function generateComparisonInsight(
  compId: number,
): Promise<ComparisonResponse> {
  return api.post(`/compare/${compId}/insights`);
}
