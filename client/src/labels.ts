// Reviewer-facing names for categories, verdicts and decisions.

import type { Category, DecisionKind, Verdict } from './api'

/** Category names in the reviewer's words. */
export const CATEGORY_NAMES: Record<Category, string> = {
  numeric: 'Numeric types',
  input: 'Input parsing',
  output: 'Output format',
  api: 'Library behaviour',
  division: 'Division and modulo',
  errors: 'Exceptions',
}

/** Gemini's verdicts in the reviewer's words. */
export const VERDICT_NAMES: Record<Verdict, string> = {
  mismatch: 'Behaves differently',
  handled: 'Handled',
  unclear: "Can't tell",
}

/** Logged decisions, as shown once made. */
export const DECISION_NAMES: Record<DecisionKind, string> = {
  confirmed: 'Confirmed bug',
  intended: 'Intended',
  dismissed: 'Dismissed',
}

/** The action buttons, with the key that triggers each. */
export const DECISION_ACTIONS: { kind: DecisionKind; label: string; key: string }[] = [
  { kind: 'confirmed', label: 'Confirm bug', key: '1' },
  { kind: 'intended', label: 'Mark intended', key: '2' },
  { kind: 'dismissed', label: 'Dismiss', key: '3' },
]
