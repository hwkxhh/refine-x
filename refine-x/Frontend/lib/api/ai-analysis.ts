import { api } from "./client";
import type {
  HeaderAnalysisResponse,
  FormulaSuggestionsResponse,
} from "./types";

/** AI reviews all columns — marks unnecessary vs essential. */
export function analyzeHeaders(jobId: number): Promise<HeaderAnalysisResponse> {
  return api.get(`/jobs/${jobId}/analyze-headers`);
}

/** Drop selected columns from the cached dataset. */
export function dropColumns(jobId: number, columns: string[]): Promise<void> {
  return api.post(`/jobs/${jobId}/drop-columns`, { columns });
}

/** AI suggests calculations & chart pairings for the data. */
export function getFormulaSuggestions(
  jobId: number,
): Promise<FormulaSuggestionsResponse> {
  return api.get(`/jobs/${jobId}/formula-suggestions`);
}
