// Reduce the append-only decision log to the current call on each flag.

import type { Decision } from './api'

/**
 * Keep the latest decision on each flag of one review.
 *
 * The log keeps every decision, so a changed mind is a later entry, not an edit.
 *
 * @param log Decisions on one sample, oldest first, as the API returns them.
 * @param run The run being reviewed, or null for a live analysis.
 * @returns The latest decision by flag id, for that run only.
 */
export function latestByFlag(log: Decision[], run: string | null): Map<string, Decision> {
  const latest = new Map<string, Decision>()
  for (const decision of log) {
    if (decision.run === run) latest.set(decision.flag.id, decision)
  }
  return latest
}
