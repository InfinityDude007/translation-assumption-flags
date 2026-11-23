// Tests for splitting highlighted code into self-contained lines.

import { describe, expect, it } from 'vitest'
import { highlightLines } from './highlight'

/** Count opening and closing span tags. */
const balance = (html: string) => (html.match(/<span/g) ?? []).length - (html.match(/<\/span>/g) ?? []).length

describe('highlightLines', () => {
  it('gives one entry per line, without a trailing empty line', () => {
    expect(highlightLines('a = 1\nb = 2\n', 'python')).toHaveLength(2)
  })

  it('closes and reopens spans that cross a line break', () => {
    const lines = highlightLines('/* one\n two */\nint x;', 'java')
    expect(lines).toHaveLength(3)
    for (const line of lines) expect(balance(line)).toBe(0)
    expect(lines[1]).toContain('hljs-comment')
  })

  it('escapes the code', () => {
    expect(highlightLines('if (a < b) {}', 'java')[0]).toContain('&lt;')
  })
})
