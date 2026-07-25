import type { Scan, ScanProgress, ScanResult } from "../types";
import { CLEAN_RESULT, VULNERABLE_RESULT } from "./fixtures";

const PHASES: ReadonlyArray<readonly [string, string]> = [
  ["resolving", "Checking the target is safe to reach"],
  ["fetching_page", "Fetching the page"],
  ["parsing_assets", "Finding scripts and assets"],
  ["scanning_bundles", "Reading JavaScript bundles"],
  ["probing_paths", "Checking for exposed files"],
  ["fingerprinting", "Identifying the platform"],
  ["footprint", "Checking DNS, mail and certificates"],
  ["scoring", "Scoring findings"],
];

const QUEUE_MS = 1200;
const PHASE_MS = 1300;
const RUN_MS = PHASES.length * PHASE_MS;

interface MockRecord {
  id: string;
  url: string;
  createdAt: number;
  clean: boolean;
}

const scans = new Map<string, MockRecord>();

export class MockError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

const PRIVATE_HOST =
  /^(localhost|127\.|10\.|192\.168\.|169\.254\.|172\.(1[6-9]|2\d|3[01])\.|\[?::1\]?$)/i;

function parseTarget(raw: unknown): URL {
  if (typeof raw !== "string" || raw.trim() === "") {
    throw new MockError("invalid_url", "Enter the URL of your app.", 400);
  }
  const candidate = raw.trim().includes("://") ? raw.trim() : `https://${raw.trim()}`;

  let url: URL;
  try {
    url = new URL(candidate);
  } catch {
    throw new MockError(
      "invalid_url",
      "That does not look like a valid URL. Try something like https://myapp.lovable.app",
      400,
    );
  }

  if (url.protocol !== "https:" && url.protocol !== "http:") {
    throw new MockError("invalid_url", "Only http and https URLs can be scanned.", 400);
  }

  if (
    PRIVATE_HOST.test(url.hostname) ||
    url.hostname.endsWith(".local") ||
    url.hostname.endsWith(".internal")
  ) {
    throw new MockError(
      "blocked_target",
      "That address is on a private network and cannot be reached. Only publicly reachable apps can be scanned.",
      422,
    );
  }

  return url;
}

/** Rewrites fixture hostnames to the submitted one so the demo report reads coherently. */
function personalise(result: ScanResult, target: URL): ScanResult {
  const fixture = new URL(result.url);
  const json = JSON.stringify(result)
    .split(fixture.origin)
    .join(target.origin)
    .split(fixture.hostname)
    .join(target.hostname);
  return JSON.parse(json) as ScanResult;
}

export function createMockScan(rawUrl: unknown): Scan {
  const target = parseTarget(rawUrl);
  const id = `scn_${crypto.randomUUID().replace(/-/g, "").slice(0, 16)}`;
  const record: MockRecord = {
    id,
    url: target.toString(),
    createdAt: Date.now(),
    clean: /clean|secure|safe/i.test(target.hostname),
  };
  scans.set(id, record);
  return toScan(record);
}

export function getMockScan(id: string): Scan {
  const record = scans.get(id);
  if (!record) {
    throw new MockError(
      "scan_not_found",
      "This scan link has expired or does not exist.",
      404,
    );
  }
  return toScan(record);
}

function toScan(record: MockRecord): Scan {
  const elapsed = Date.now() - record.createdAt;
  const created = new Date(record.createdAt).toISOString();
  const base = {
    id: record.id,
    url: record.url,
    tier: "passive" as const,
    created_at: created,
    error: null,
  };

  if (elapsed < QUEUE_MS) {
    return {
      ...base,
      status: "queued",
      started_at: null,
      completed_at: null,
      progress: null,
      result: null,
      poll_after_ms: 700,
    };
  }

  const startedAt = new Date(record.createdAt + QUEUE_MS).toISOString();

  if (elapsed < QUEUE_MS + RUN_MS) {
    const index = Math.min(
      PHASES.length - 1,
      Math.floor((elapsed - QUEUE_MS) / PHASE_MS),
    );
    const [phase, label] = PHASES[index];
    const progress: ScanProgress = {
      phase,
      label,
      completed: index,
      total: PHASES.length,
    };
    return {
      ...base,
      status: "running",
      started_at: startedAt,
      completed_at: null,
      progress,
      result: null,
      poll_after_ms: 900,
    };
  }

  const source = record.clean ? CLEAN_RESULT : VULNERABLE_RESULT;
  return {
    ...base,
    status: "complete",
    started_at: startedAt,
    completed_at: new Date(record.createdAt + QUEUE_MS + RUN_MS).toISOString(),
    progress: null,
    result: personalise(source, new URL(record.url)),
    poll_after_ms: 0,
  };
}
