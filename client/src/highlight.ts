// Syntax highlighting split into lines, so each line can be marked on its own.

import hljs from 'highlight.js/lib/core'
import java from 'highlight.js/lib/languages/java'
import python from 'highlight.js/lib/languages/python'

hljs.registerLanguage('python', python)
hljs.registerLanguage('java', java)

/**
 * Highlight a file and split the HTML into one string per line.
 *
 * Spans that cross a line break, such as a block comment, are closed at the
 * end of the line and reopened on the next, so every line is valid HTML.
 *
 * @param code The file's text.
 * @param language 'python' or 'java'.
 * @returns Escaped, highlighted HTML for each line.
 */
export function highlightLines(code: string, language: 'python' | 'java'): string[] {
  const html = hljs.highlight(code.replace(/\n$/, ''), { language, ignoreIllegals: true }).value
  const lines: string[] = []
  const open: string[] = []
  let line = ''
  for (const token of html.split(/(<span[^>]*>|<\/span>|\n)/)) {
    if (token === '\n') {
      lines.push(line + '</span>'.repeat(open.length))
      line = open.join('')
    } else {
      if (token.startsWith('<span')) open.push(token)
      else if (token === '</span>') open.pop()
      line += token
    }
  }
  lines.push(line)
  return lines
}
