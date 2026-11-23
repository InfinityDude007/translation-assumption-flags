// Choosing where the shown flags come from.

import type { RunSummary } from './api'

/** The value of the "Flags from" picker that means a live analysis. */
export const LIVE = 'live'

/**
 * Pick the run to show first: the latest prompt version, among runs that cover
 * every sample if any do, and the newest run within that version.
 *
 * @param runs The archived runs.
 * @param total How many samples there are.
 * @returns The run's name, or LIVE if there are no runs.
 */
export function defaultRun(runs: RunSummary[], total: number): string {
  const complete = runs.filter((run) => run.samples === total)
  const ranked = [...(complete.length > 0 ? complete : runs)].sort(
    (a, b) =>
      b.prompt_version.localeCompare(a.prompt_version, undefined, { numeric: true }) ||
      b.created_at.localeCompare(a.created_at),
  )
  return ranked[0]?.name ?? LIVE
}
