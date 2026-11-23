// Tests for the messages shown when an API call fails.

import { describe, expect, it } from 'vitest'
import { ApiError } from './api'
import { describeError } from './errors'

describe('describeError', () => {
  it.each([
    [new ApiError(429, 'RESOURCE_EXHAUSTED'), 'daily request limit'],
    [new ApiError(503, 'set GEMINI_API_KEY in server/.env'), 'No Gemini key is set'],
    [new ApiError(503, 'UNAVAILABLE'), 'overloaded'],
    [new ApiError(502, 'bad json'), "Gemini's reply could not be used: bad json"],
    [new ApiError(422, 'not valid Python'), 'not valid Python'],
    [new ApiError(404, "no sample 'x'"), "no sample 'x'"],
  ])('explains %s', (error, expected) => {
    expect(describeError(error)).toContain(expected)
  })
})
