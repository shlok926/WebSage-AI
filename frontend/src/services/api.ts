/**
 * WebSage AI — Frontend API Client.
 *
 * Communicates with the FastAPI backend according to the Requirements v1.2 contract.
 */

export interface SummarizeSuccessResponse {
  summary: string;
  source_url: string;
  source_host: string;
  extracted_characters: number;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

// In local dev, empty string leverages Vite proxy. In production, use configured env var.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function summarizeUrl(url: string): Promise<SummarizeSuccessResponse> {
  const endpoint = `${API_BASE_URL}/api/summarize`;

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ url }),
    });
  } catch (err) {
    throw new Error('Unable to connect to WebSage AI server. Please verify your connection.');
  }

  const data = await response.json();

  if (!response.ok) {
    const errorData = data as ApiErrorResponse;
    const message = errorData?.error?.message || `Request failed with status ${response.status}.`;
    const code = errorData?.error?.code || 'UNKNOWN_ERROR';
    const error = new Error(message);
    (error as any).code = code;
    throw error;
  }

  return data as SummarizeSuccessResponse;
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) return false;
    const data = await response.json();
    return data?.status === 'ok';
  } catch {
    return false;
  }
}
