import { BRAND } from "./brand";
import type { Scan } from "./types";

/**
 * Always same-origin. app/api/v1/[...path] proxies to OVERSHARE_API_URL at request
 * time, so the backend location stays a runtime env var and no CORS is involved.
 */
const BASE = "/api/v1";

export class ApiRequestError extends Error {
  readonly code: string;
  readonly status: number;
  readonly retryAfterSeconds: number | null;

  constructor(
    code: string,
    message: string,
    status: number,
    retryAfterSeconds: number | null = null,
  ) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.status = status;
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      ...init,
      cache: "no-store",
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiRequestError(
      "network_error",
      `Could not reach ${BRAND.name}. Check your connection and try again.`,
      0,
    );
  }

  if (!response.ok) {
    const retryAfter = Number(response.headers.get("Retry-After"));
    let code = "internal_error";
    let message = "Something went wrong. Please try again.";
    try {
      const body = await response.json();
      if (body?.error?.code) code = body.error.code;
      if (body?.error?.message) message = body.error.message;
    } catch {
      // Non-JSON error body (proxy timeout, gateway page). Keep the defaults.
    }
    throw new ApiRequestError(
      code,
      message,
      response.status,
      Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter : null,
    );
  }

  return response.json() as Promise<T>;
}

export function createScan(url: string): Promise<Scan> {
  return request<Scan>("/scans", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function getScan(id: string): Promise<Scan> {
  return request<Scan>(`/scans/${encodeURIComponent(id)}`);
}
