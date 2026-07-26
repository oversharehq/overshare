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
      {/* A ruled line to write on rather than a boxed widget — the input reads
          as a field on a form, which is what it is. */}
      <div className="flex items-stretch border-b-2 border-ink focus-within:border-flag">
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
          className="min-w-0 flex-1 bg-transparent py-3.5 pr-3 font-mono text-[0.9rem] text-ink outline-none focus-visible:outline-none placeholder:text-faint"
        />
        <button
          type="submit"
          disabled={pending || url.trim() === ""}
          className="label shrink-0 self-stretch bg-ink px-6 text-paper transition-colors hover:bg-flag disabled:bg-rule-firm disabled:text-paper"
        >
          {pending ? "Starting…" : "Scan →"}
        </button>
      </div>

      {error && (
        <p
          id="scan-error"
          role="alert"
          className="mt-3 border-l-2 border-flag bg-flag-wash px-3 py-2 font-mono text-xs leading-relaxed text-flag"
        >
          {error}
        </p>
      )}

      <p className="mt-3 font-mono text-xs text-mute">
        No signup. Takes about a minute. Only scan apps you own.
      </p>
    </form>
  );
}
