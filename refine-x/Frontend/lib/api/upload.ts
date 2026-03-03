import { api } from "./client";
import type {
  UploadJobResponse,
  UploadJobListResponse,
  JobStatusResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Upload a CSV / XLSX file.
 * Uses multipart/form-data — must NOT set Content-Type manually.
 */
export async function uploadFile(file: File): Promise<UploadJobResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;

  const res = await fetch(`${API_URL}/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw { detail: err.detail || "Upload failed", status: res.status };
  }

  return res.json();
}

/** List all upload jobs for the current user. */
export function listJobs(): Promise<UploadJobListResponse[]> {
  return api.get("/upload/jobs");
}

/** Get full details of a single job. */
export function getJob(jobId: number): Promise<UploadJobResponse> {
  return api.get(`/upload/jobs/${jobId}`);
}

/** Poll job status + progress. */
export function getJobStatus(jobId: number): Promise<JobStatusResponse> {
  return api.get(`/upload/jobs/${jobId}/status`);
}

/** Delete a job. */
export function deleteJob(jobId: number): Promise<void> {
  return api.delete(`/upload/jobs/${jobId}`);
}

/** Submit confirmed columns after the column-relevance gate. */
export function reviewColumns(
  jobId: number,
  confirmedColumns: string[],
): Promise<UploadJobResponse> {
  return api.post(`/upload/jobs/${jobId}/review`, {
    confirmed_columns: confirmedColumns,
  });
}
