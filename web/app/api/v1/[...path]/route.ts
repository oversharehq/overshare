import { mockDisabledResponse } from "@/lib/mock/guard";
import { MockError, createMockScan, getMockScan } from "@/lib/mock/store";

/**
 * Single boundary between the browser and the scanner API.
 *
 * This is a request-time proxy rather than a next.config rewrite because
 * rewrites are resolved at build time and baked into the routes manifest — the
 * backend URL would have to be known when the image is built, which defeats
 * promoting one image between environments. Proxying here also keeps every call
 * same-origin, so the API never needs CORS.
 *
 * With no backend configured the request falls through to the mock, which
 * refuses to run in production. See lib/mock/guard.ts.
 */

const SAFE_SEGMENT = /^[\w.~-]+$/;
const UPSTREAM_TIMEOUT_MS = 15_000;

function jsonError(code: string, message: string, status: number): Response {
  return Response.json({ error: { code, message } }, { status });
}

function upstreamBase(): string | null {
  const base = process.env.LEAKSCAN_API_URL?.replace(/\/+$/, "");
  return base && base.length > 0 ? base : null;
}

async function handle(
  request: Request,
  context: RouteContext<"/api/v1/[...path]">,
): Promise<Response> {
  const { path } = await context.params;
  const segments = path ?? [];

  // The segments are interpolated into an outbound URL, so anything that could
  // redirect the request off the configured host is rejected outright.
  if (segments.some((segment) => !SAFE_SEGMENT.test(segment))) {
    return jsonError("not_found", "Unknown endpoint.", 404);
  }

  const base = upstreamBase();
  return base
    ? proxy(request, base, segments)
    : mock(request, segments);
}

async function proxy(
  request: Request,
  base: string,
  segments: string[],
): Promise<Response> {
  const search = new URL(request.url).search;
  const target = `${base}/v1/${segments.join("/")}${search}`;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  // Lets the API apply per-client rate limits rather than seeing only this server.
  const forwardedFor = request.headers.get("x-forwarded-for");
  if (forwardedFor) headers.set("x-forwarded-for", forwardedFor);

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers,
      body: request.method === "GET" || request.method === "HEAD"
        ? undefined
        : await request.text(),
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
      redirect: "manual",
      cache: "no-store",
    });
  } catch {
    return jsonError(
      "internal_error",
      "The scanner is not responding. Please try again shortly.",
      502,
    );
  }

  const responseHeaders = new Headers();
  for (const header of ["content-type", "retry-after"]) {
    const value = upstream.headers.get(header);
    if (value) responseHeaders.set(header, value);
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

async function mock(request: Request, segments: string[]): Promise<Response> {
  const disabled = mockDisabledResponse();
  if (disabled) return disabled;

  try {
    if (segments[0] === "scans" && segments.length === 1 && request.method === "POST") {
      let body: unknown;
      try {
        body = await request.json();
      } catch {
        return jsonError("invalid_url", "Enter the URL of your app.", 400);
      }
      return Response.json(createMockScan((body as { url?: unknown })?.url), {
        status: 202,
        headers: { "X-LeakScan-Mock": "1" },
      });
    }

    if (segments[0] === "scans" && segments.length === 2 && request.method === "GET") {
      return Response.json(getMockScan(segments[1]), {
        headers: { "X-LeakScan-Mock": "1" },
      });
    }
  } catch (error) {
    if (error instanceof MockError) {
      return jsonError(error.code, error.message, error.status);
    }
    throw error;
  }

  return jsonError("not_found", "Unknown endpoint.", 404);
}

export { handle as GET, handle as POST };
