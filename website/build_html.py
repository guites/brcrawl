#!/usr/bin/env python3
"""Reads a JSON feed file and generates paginated HTML pages styled like tinyfeed."""

import argparse
import json
import math
import secrets
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ITEMS_PER_PAGE = 50

CSS = """\
:root {
    color-scheme: dark light;
    --primary: #0AC8F5;
    --secondary: #D2F00F;
    --text: var(--txt, #cfcfcf);
    --border: var(--bd, #c0c0c0);
    --background: var(--bg, #1D1F21);
    font-size: min(calc(.5rem + 0.75vw), 16px);
}

@media (prefers-color-scheme: light) {
    :root {
        --text: var(--txt, #444444);
        --border: var(--bd, #333333);
        --background: var(--bg, white);
        --primary: #207D92;
        --secondary: #6A7A06;
    }
}

body {
    font-family: Calibri, 'Trebuchet MS', 'Lucida Sans', Arial, sans-serif;
    color: var(--text);
    background: var(--background);
    max-width: 50rem;
    width: 100%;
    margin: 0.5em auto 2em;
    line-height: 1.25em;
}

header {
    border-bottom: 1px solid var(--border);
    margin-bottom: 0.25em;
}

header > h1 {
    display: inline-block;
    padding: 0 0.5em;
}

h2 {
    font-size: 1rem;
    display: inline;
}

ol {
    padding-left: 5ch;
}

li {
    margin-block-start: 1em;
}

a {
    text-decoration: none;
}

a:link {
    color: var(--primary);
}

a:visited {
    color: var(--secondary);
}

a:hover {
    opacity: 0.8;
}

small {
    padding-top: 0.25rem;
    font-size: 0.95rem;
}

small > a:link,
small > a:visited {
    color: var(--text);
}

footer {
    padding: 1rem;
    margin-top: 2rem;
    border-top: 1px solid var(--border);
}

nav {
    display: flex;
    justify-content: center;
    gap: 1em;
    padding: 1em 0;
    border-top: 1px solid var(--border);
    margin-top: 1em;
}

nav > a, nav > span {
    padding: 0.25em 0.75em;
}

nav > span {
    color: var(--border);
}"""


def page_filename(page_num: int) -> str:
    """Return the filename for a given page number (1-indexed)."""
    if page_num == 1:
        return "index.html"
    return f"page-{page_num}.html"


def render_items_html(items: list[dict], start_index: int) -> str:
    """Render the <ol> block for a list of items."""
    lines = [f'\t\t<ol start="{start_index}">']
    for item in items:
        link = escape(item.get("link", ""), quote=True)
        title = escape(item.get("title", "Untitled"))
        publication = escape(item.get("publication", ""))
        domain = escape(item.get("domain", ""))
        lines.append("\t\t\t<li>")
        lines.append(f'\t\t\t\t<a href="{link}" target="_blank">')
        lines.append(f"\t\t\t\t\t<h2>{title}</h2>")
        lines.append("\t\t\t\t</a>")
        lines.append("\t\t\t\t<br>")
        lines.append("\t\t\t\t<small>")
        lines.append(
            f'\t\t\t\t\t<time datetime="{publication}">{publication}</time>'
        )
        lines.append("\t\t\t\t\t|")
        lines.append(
            f'\t\t\t\t\t<a href="https://{domain}" target="_blank">{domain}</a>'
        )
        lines.append("\t\t\t\t</small>")
        lines.append("\t\t\t</li>")
    lines.append("\t\t</ol>")
    return "\n".join(lines)


def render_nav(current_page: int, total_pages: int) -> str:
    """Render the pagination nav bar."""
    if total_pages <= 1:
        return ""

    parts = ["\t\t<nav>"]
    if current_page > 1:
        prev_file = page_filename(current_page - 1)
        parts.append(f'\t\t\t<a href="{prev_file}">&larr; Previous</a>')
    else:
        parts.append("\t\t\t<span>&larr; Previous</span>")

    parts.append(f"\t\t\t<span>Page {current_page} of {total_pages}</span>")

    if current_page < total_pages:
        next_file = page_filename(current_page + 1)
        parts.append(f'\t\t\t<a href="{next_file}">Next &rarr;</a>')
    else:
        parts.append("\t\t\t<span>Next &rarr;</span>")

    parts.append("\t\t</nav>")
    return "\n".join(parts)


def render_page(
    items: list[dict],
    page_num: int,
    total_pages: int,
    start_index: int,
    name: str,
    description: str,
) -> str:
    """Render a full HTML page."""
    nonce = secrets.token_hex(16)
    now = datetime.now(timezone.utc)
    day = now.strftime("%A")
    dt_display = now.strftime("%Y-%m-%d %H:%M:%S")
    dt_rfc3339 = now.isoformat()

    items_html = render_items_html(items, start_index)
    nav_html = render_nav(page_num, total_pages)

    return f"""\
<!DOCTYPE html>
<html lang="en" dir="ltr">

<head>
\t<meta charset="UTF-8">
\t<meta name="viewport" content="width=device-width, initial-scale=1">

\t<title>{escape(name)}</title>

\t<meta http-equiv="Content-Security-Policy" content="
\t\tdefault-src 'none';
\t\tbase-uri 'self';
\t\timg-src 'self' data: ;
\t\tstyle-src 'nonce-{nonce}' ;
\t\tscript-src 'nonce-{nonce}' 'strict-dynamic' ;
\t">
\t<meta name="application-name" content="brcrawl">
\t<meta name="description" content="{escape(description, quote=True)}">
\t<meta name="referrer" content="same-origin">

\t<style nonce="{nonce}">
{CSS}
\t</style>
</head>

<body>
\t<header>
\t\t<h1>{escape(name)}</h1>
\t\t{escape(description)}
\t</header>
\t<main>
{items_html}
{nav_html}
\t</main>
\t<footer>
\t\t<p>Last Updated On:
\t\t\t<time id="update-at" datetime="{dt_rfc3339}">
\t\t\t\t{day}, {dt_display}
\t\t\t</time>
\t\t</p>
\t</footer>
</body>

<script type="module" nonce="{nonce}">
\tconst updatedAtElement = document.getElementById("update-at");
\tconst date = new Date(updatedAtElement.dateTime);
\tupdatedAtElement.innerText = date.toLocaleString(undefined, {{
\t\tdateStyle: "full",
\t\ttimeStyle: "medium",
\t}})
</script>

</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate paginated HTML pages from a JSON feed file."
    )
    parser.add_argument("input", help="Path to the JSON feed file")
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Directory to write HTML files to (default: current directory)",
    )
    parser.add_argument(
        "-n", "--name", default="BR Crawl", help="Page title (default: BR Crawl)"
    )
    parser.add_argument(
        "-d",
        "--description",
        default="Diretório da smallweb brasileira",
        help="Page description",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path) as f:
        items = json.load(f)

    if not isinstance(items, list):
        print("Error: JSON file must contain an array of objects", file=sys.stderr)
        sys.exit(1)

    total_pages = max(1, math.ceil(len(items) / ITEMS_PER_PAGE))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        page_items = items[start:end]
        start_index = start + 1  # 1-indexed for <ol start="">

        html = render_page(
            page_items,
            page_num,
            total_pages,
            start_index,
            args.name,
            args.description,
        )

        out_path = output_dir / page_filename(page_num)
        out_path.write_text(html)
        print(f"Generated {out_path} ({len(page_items)} items)")

    print(f"Done: {total_pages} page(s), {len(items)} items total")


if __name__ == "__main__":
    main()
