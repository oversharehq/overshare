"use client";

import { useState } from "react";
import type { Finding } from "@/lib/types";
import { FindingCard } from "./FindingCard";

export function FindingsList({ findings }: { findings: Finding[] }) {
  const [showInfo, setShowInfo] = useState(false);

  const actionable = findings.filter((finding) => finding.severity !== "info");
  const informational = findings.filter((finding) => finding.severity === "info");

  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold text-slate-900">Findings</h2>

      {actionable.length === 0 ? (
        <p className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          Nothing actionable on the public surface. That is a genuinely good
          result — but read the scope notes below, because it does not mean the
          app is secure overall.
        </p>
      ) : (
        <div className="mt-3 space-y-3">
          {actionable.map((finding) => (
            <FindingCard key={`${finding.check_id}:${finding.location}`} finding={finding} />
          ))}
        </div>
      )}

      {informational.length > 0 && (
        <div className="mt-6">
          <button
            type="button"
            onClick={() => setShowInfo((value) => !value)}
            aria-expanded={showInfo}
            className="print-hidden text-sm font-medium text-slate-600 underline underline-offset-4 hover:text-slate-900"
          >
            {showInfo ? "Hide" : "Show"} {informational.length} informational{" "}
            {informational.length === 1 ? "note" : "notes"}
          </button>

          {showInfo && (
            <div className="mt-3 space-y-3">
              {informational.map((finding) => (
                <FindingCard
                  key={`${finding.check_id}:${finding.location}`}
                  finding={finding}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
