// Tests for choosing the run shown first.

import { describe, expect, it } from 'vitest'
import type { RunSummary } from './api'
import { defaultRun, LIVE } from './runs'

/** An archived run. */
const run = (name: string, prompt_version: string, created_at: string, samples = 35): RunSummary => ({
  name,
  model: 'gemini-test',
  prompt_version,
  created_at,
  samples,
})

describe('defaultRun', () => {
  it('prefers the latest prompt version over the newest start time', () => {
    const runs = [run('v2', '2', '2026-11-21'), run('v1b', '1', '2026-11-22')]
    expect(defaultRun(runs, 35)).toBe('v2')
  })

  it('skips incomplete runs when a complete one exists', () => {
    const runs = [run('v2', '2', '2026-11-21'), run('flash-v3', '3', '2026-11-23', 3)]
    expect(defaultRun(runs, 35)).toBe('v2')
  })

  it('compares versions as numbers', () => {
    expect(defaultRun([run('v9', '9', '2026-11-21'), run('v10', '10', '2026-11-20')], 35)).toBe('v10')
  })

  it('falls back to live analysis without runs', () => {
    expect(defaultRun([], 35)).toBe(LIVE)
  })
})
