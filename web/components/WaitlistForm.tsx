"use client";

import { useState } from "react";
import { ApiRequestError, joinWaitlist } from "@/lib/api";

export function WaitlistForm() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [joined, setJoined] = useState(false);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending) return;

    setError(null);
    setPending(true);
    try {
      await joinWaitlist(email);
      setJoined(true);
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

  if (joined) {
    return (
      <p
        role="status"
        className="max-w-[36rem] border-l-2 border-pass bg-pass-wash px-3 py-2 font-mono text-xs leading-relaxed text-pass"
      >
        On the list. We&rsquo;ll email you once Cloud is ready — nothing else.
      </p>
    );
  }

  return (
    <form onSubmit={onSubmit} noValidate className="max-w-[36rem]">
      <div className="flex items-stretch border-b-2 border-ink focus-within:border-flag">
        <input
          type="email"
          name="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@company.com"
          aria-label="Email address for the Cloud waitlist"
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? "waitlist-error" : undefined}
          className="min-w-0 flex-1 bg-transparent py-3.5 pr-3 font-mono text-[0.9rem] text-ink outline-none focus-visible:outline-none placeholder:text-faint"
        />
        <button
          type="submit"
          disabled={pending || email.trim() === ""}
          className="label shrink-0 self-stretch bg-ink px-6 text-paper transition-colors hover:bg-flag disabled:bg-rule-firm disabled:text-paper"
        >
          {pending ? "Adding…" : "Notify me →"}
        </button>
      </div>

      {error && (
        <p
          id="waitlist-error"
          role="alert"
          className="mt-3 border-l-2 border-flag bg-flag-wash px-3 py-2 font-mono text-xs leading-relaxed text-flag"
        >
          {error}
        </p>
      )}

      <p className="mt-3 font-mono text-xs text-mute">
        One email when it launches. No newsletter, no sharing.
      </p>
    </form>
  );
}
