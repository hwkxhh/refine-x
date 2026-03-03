import { api } from "./client";
import type {
  CleaningSummaryResponse,
  AuditLogEntry,
  MissingFieldsResponse,
  OutliersResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Get cleaning summary (rows before/after, quality score, column metadata). */
export function getCleaningSummary(jobId: number): Promise<CleaningSummaryResponse> {
  return api.get(`/jobs/${jobId}/cleaning-summary`);
}

/** Get paginated audit trail. */
export function getAuditTrail(
  jobId: number,
  page = 1,
  perPage = 50,
): Promise<AuditLogEntry[]> {
  return api.get(`/jobs/${jobId}/audit-trail?page=${page}&per_page=${perPage}`);
}

/** Get columns with missing values and suggested fill strategies. */
export function getMissingFields(jobId: number): Promise<MissingFieldsResponse> {
  return api.get(`/jobs/${jobId}/missing-fields`);
}

/** Manually fill specific cells. */
export function fillMissing(
  jobId: number,
  column: string,
  rowIndices: number[],
  values: string[],
): Promise<void> {
  return api.post(`/jobs/${jobId}/fill-missing`, {
    column,
    row_indices: rowIndices,
    values,
  });
}

/** Get flagged outliers. */
export function getOutliers(jobId: number): Promise<OutliersResponse> {
  return api.get(`/jobs/${jobId}/outliers`);
}

/** Keep or remove an outlier. */
export function resolveOutlier(
  jobId: number,
  rowIndex: number,
  action: "keep" | "remove",
): Promise<void> {
  return api.post(`/jobs/${jobId}/resolve-outlier`, {
    row_index: rowIndex,
    action,
  });
}

/** Download cleaned CSV as a Blob. */
export async function exportCSV(jobId: number): Promise<Blob> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;

  const res = await fetch(`${API_URL}/jobs/${jobId}/export`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!res.ok) throw new Error("Export failed");
  return res.blob();
}
