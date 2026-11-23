// Tests for reducing the decision log to the latest call on each flag.

import { describe, expect, it } from 'vitest'
import type { Decision, DecisionKind } from './api'
import { latestByFlag } from './decisions'

/** A logged decision on a flag, from a run. */
function logged(flagId: string, decision: DecisionKind, run: string | null): Decision {
  const flag = {
    id: flagId,
    site: { rule: 'floor_division', category: 'division' as const, line: 2, end_line: 2, snippet: 'n // 2', reason: '' },
    verdict: 'mismatch' as const,
    translation_lines: [5],
    assumption: '',
    suggestion: null,
  }
  return { sample_id: 's', run, model: 'm', prompt_version: '2', flag, decision, note: '', decided_at: '' }
}

describe('latestByFlag', () => {
  it('keeps the last decision on each flag', () => {
    const log = [logged('division-2', 'confirmed', 'r'), logged('input-1', 'intended', 'r'), logged('division-2', 'dismissed', 'r')]
    const latest = latestByFlag(log, 'r')
    expect(latest.get('division-2')?.decision).toBe('dismissed')
    expect(latest.get('input-1')?.decision).toBe('intended')
  })

  it('ignores decisions made on other runs or live analyses', () => {
    const log = [logged('division-2', 'confirmed', 'other'), logged('division-2', 'intended', null)]
    expect(latestByFlag(log, 'r').size).toBe(0)
    expect(latestByFlag(log, null).get('division-2')?.decision).toBe('intended')
  })
})
