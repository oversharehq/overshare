"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiRequestError, createScan } from "@/lib/api";

export function ScanForm({
  autoFocus = false,
  placeholder = "https://myapp.lovable.app",
}: {
  autoFocus?: boolean;
  placeholder?: string;
}) {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;

    setError(null);
    setPending(true);
    try {
      const scan = await createScan(url);
      router.push(`/scan/${scan.id}`);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(
          err.retryAfterSeconds
            ? `${err.message} Try again in ${err.retryAfterSeconds} seconds.`
            : err.message,
        );
      } else {
        setError("Something went wrong. Please try again.");
      }
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} noValidate>
      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          type="url"
          name="url"
          value={url}
          autoFocus={autoFocus}
          onChange={(event) => setUrl(event.target.value)}
          placeholder={placeholder}
          aria-label="URL of the app to scan"
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? "scan-error" : undefined}
          className="w-full flex-1 rounded-md border border-slate-300 bg-white px-4 py-3 font-mono text-sm text-slate-900 shadow-sm outline-none placeholder:text-slate-400 focus:border-slate-900 focus:ring-2 focus:ring-slate-900/10"
        />
        <button
          type="submit"
          disabled={pending || url.trim() === ""}
          className="rounded-md bg-slate-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {pending ? "Starting…" : "Scan for free"}
        </button>
      </div>

      {error && (
        <p
          id="scan-error"
          role="alert"
          className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
        >
          {error}
        </p>
      )}

      <p className="mt-3 text-xs text-slate-500">
        No signup. Takes about a minute. Only scan apps you own.
      </p>
    </form>
  );
}
