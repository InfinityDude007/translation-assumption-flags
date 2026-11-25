import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

START = "<!-- coverage:start -->"
END = "<!-- coverage:end -->"
PREFIX = "src/server/"


def colour_picker(percent: float) -> str:
    if percent >= 90:
        return "#4c1"
    if percent >= 75:
        return "#97ca00"
    if percent >= 60:
        return "#dfb317"
    return "#e05d44"


def badge(percent: float) -> str:
    value = f"{percent:.0f}%"
    left, right = 63, 10 + 7 * len(value)
    width = left + right
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="coverage: {value}">
<title>coverage: {value}</title>
<linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
<clipPath id="r"><rect width="{width}" height="20" rx="3" fill="#fff"/></clipPath>
<g clip-path="url(#r)">
<rect width="{left}" height="20" fill="#555"/>
<rect x="{left}" width="{right}" height="20" fill="{colour_picker(percent)}"/>
<rect width="{width}" height="20" fill="url(#s)"/>
</g>
<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
<text x="{left / 2}" y="15" fill="#010101" fill-opacity=".3">coverage</text>
<text x="{left / 2}" y="14">coverage</text>
<text x="{left + right / 2}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
<text x="{left + right / 2}" y="14">{value}</text>
</g>
</svg>
"""


def report(data: dict[str, Any]) -> str:
    """Render the total and a per-file table as Markdown."""
    totals, files = data["totals"], data["files"]
    commit = os.environ.get("GITHUB_SHA", "local")[:7]
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    lines = [
        f"**Total: {totals['percent_covered']:.0f}%** of {totals['num_statements']} "
        f"statements ({totals['missing_lines']} missed), from the pytest suite "
        f"on commit `{commit}`, {date}. Updated by the Coverage workflow.",
        "",
        "<details>",
        "<summary>Coverage by file</summary>",
        "",
        "| File | Statements | Missed | Covered |",
        "|---|---:|---:|---:|",
    ]
    for path in sorted(files):
        summary = files[path]["summary"]
        name = path.removeprefix(PREFIX)
        lines.append(
            f"| `{name}` | {summary['num_statements']} | "
            f"{summary['missing_lines']} | {summary['percent_covered']:.0f}% |"
        )
    lines += ["", "</details>"]
    return "\n".join(lines)


def main() -> None:
    """Replace the README's coverage section and write the badge."""
    coverage_json, readme_md, badge_svg = (Path(arg) for arg in sys.argv[1:4])
    data = json.loads(coverage_json.read_text())
    readme = readme_md.read_text()
    if START not in readme or END not in readme:
        sys.exit(f"{readme_md} needs the {START} and {END} markers")
    before, rest = readme.split(START, 1)
    _, after = rest.split(END, 1)
    readme_md.write_text(f"{before}{START}\n{report(data)}\n{END}{after}")
    badge_svg.write_text(badge(data["totals"]["percent_covered"]))


if __name__ == "__main__":
    main()
