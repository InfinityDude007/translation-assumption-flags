// Turn API failures into sentences that say what happened and what to do.

import { ApiError } from './api'

/**
 * Describe a failed call for the reviewer.
 *
 * @param error The failure.
 * @returns The message to show.
 */
export function describeError(error: unknown): string {
  if (!(error instanceof ApiError)) return String(error)
  if (error.status === 429)
    return "Gemini's daily request limit for this key is used up. Pick an archived run, or try again after the limit resets."
  if (error.status === 503 && error.message.includes('GEMINI_API_KEY'))
    return 'No Gemini key is set. Add GEMINI_API_KEY to server/.env, then restart the API.'
  if (error.status === 503) return 'Gemini is overloaded right now. Try again in a minute.'
  if (error.status === 502) return `Gemini's reply could not be used: ${error.message}`
  if (error.status === 422) return `The program could not be analysed: ${error.message}`
  return error.message
}
