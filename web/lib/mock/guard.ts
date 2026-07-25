/**
 * A security scanner that silently serves fabricated results is worse than one
 * that is down: a fake clean report tells someone their app is safe when nothing
 * was ever checked. The mock only exists because OVERSHARE_API_URL is unset, so in
 * production that means the backend is misconfigured — fail loudly instead.
 */
export function mockDisabledResponse(): Response | null {
  if (process.env.NODE_ENV !== "production") return null;
  if (process.env.OVERSHARE_ALLOW_MOCK === "1") return null;

  return Response.json(
    {
      error: {
        code: "scanner_unavailable",
        message:
          "The scanner is not connected. No scan was run and no results are available.",
      },
    },
    { status: 503 },
  );
}
