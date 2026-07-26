"use client";

import { useState } from "react";
import type { Finding } from "@/lib/types";
import { Block } from "./Paper";
import { FindingCard } from "./FindingCard";

export function FindingsList({ findings }: { findings: Finding[] }) {
  const [showInfo, setShowInfo] = useState(false);

  const actionable = findings.filter((finding) => finding.severity !== "info");
  const informational = findings.filter((finding) => finding.severity === "info");

  return (
    <Block index="03" title="Findings">
      {actionable.length === 0 ? (
        <p className="max-w-[34rem] border-l-2 border-pass bg-pass-wash px-4 py-3 text-[0.95rem] leading-[1.6] text-pass">
          Nothing actionable on the public surface. That is a genuinely good
          result — but read the scope notes below, because it does not mean the
          app is secure overall.
        </p>
      ) : (
        <div className="border-t border-rule">
          {actionable.map((finding) => (
            <FindingCard
              key={`${finding.check_id}:${finding.location}`}
              finding={finding}
            />
          ))}
        </div>
      )}

      {informational.length > 0 && (
        <div className="mt-6">
          <button
            type="button"
            onClick={() => setShowInfo((value) => !value)}
            aria-expanded={showInfo}
            className="label print-hidden text-mute underline decoration-rule-firm underline-offset-4 transition-colors hover:text-flag"
          >
            {showInfo ? "Hide" : "Show"} {informational.length} informational{" "}
            {informational.length === 1 ? "note" : "notes"}
          </button>

          {showInfo && (
            <div className="mt-4 border-t border-rule">
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
    </Block>
  );
}
