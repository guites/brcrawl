#!/usr/bin/env python3
"""Reads a JSON feed file and generates paginated HTML pages styled like tinyfeed."""

import argparse
import json
import math
import re
import secrets
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
ITEMS_PER_PAGE = 50
BACKEND_URL = os.environ['BACKEND_URL']

JS = """\
var backend_url='"""+BACKEND_URL+"""';
function hide_feedback(domain) {
    return `<div><small>Domínio <a href="https://${domain}">${domain}</a> escondido. | <button class="show">exibir</button></small></div>`;
}

function report_feedback(li) {
    li.style.opacity = 0.5;
    const btn = li.querySelector("button.report");
    btn.textContent = "reportado";
    btn.className = "unreport";
}

var reported = localStorage.getItem('reported') || '[]';
reported = JSON.parse(reported);
var hidden = localStorage.getItem('hidden') || '[]';
hidden = JSON.parse(hidden);

let domains = Array.from(document.getElementsByClassName("domain"));
domains.forEach((domain) => {
    if (reported.includes(domain.textContent)) {
        const li = domain.closest("li");
        report_feedback(li);
    }
    if (hidden.includes(domain.textContent)) {
        domain.closest("li").innerHTML = hide_feedback(domain.textContent);
    }
});

function report(btn) {
    const li = btn.closest("li");
    const articleDomain = li.querySelector("a.domain");
    const domain = articleDomain.textContent;

    if (reported.length == 0) {
        const agreed = confirm("Reporte sites que não são blogs pessoais ou não estão em português. Confirme para não ver mais essa mensagem. Obrigado!");
        if (!agreed) {
            return;
        }
    }
    fetch(`${backend_url}/report`, {
        method: "POST",
        body: JSON.stringify({ domain }),
        headers: {
            "Content-Type": "application/json"
        }
    });
    reported.push(domain);
    localStorage.setItem('reported', JSON.stringify(reported));
    report_feedback(li);
}

function unreport(btn) {
    const li = btn.closest("li");
    const articleDomain = li.querySelector("a.domain");
    const domain = articleDomain.textContent;
    reported = reported.filter((d) => d != domain);
    localStorage.setItem('reported', JSON.stringify(reported));
    fetch(`${backend_url}/report`, {
        method: "POST",
        body: JSON.stringify({ domain }),
        headers: {
            "Content-Type": "application/json"
        }
    }).finally(() => {
        window.location.reload();
    });
}

function hide(btn) {
    const li = btn.closest("li");
    const articleDomain = li.querySelector("a.domain");
    const domain = articleDomain.textContent;

    hidden.push(domain);
    localStorage.setItem('hidden', JSON.stringify(hidden));
    li.innerHTML = hide_feedback(domain);
}

function show(btn) {
    const li = btn.closest("li");
    const articleDomain = li.querySelector("a");
    const domain = articleDomain.textContent;
    hidden = hidden.filter((d) => d != domain);
    localStorage.setItem('hidden', JSON.stringify(hidden));
    window.location.reload();
}

document.addEventListener("click", function(e) {
    if (e.target.className == "report") {
        return report(e.target);
    }
    if (e.target.className == "unreport") {
        return unreport(e.target);
    }
    if (e.target.className == "hide") {
        return hide(e.target);
    }
    if (e.target.className == "show") {
        return show(e.target);
    }
});"""

CSS = """\
:root {
    color-scheme: dark light;
    --primary: #0AC8F5;
    --secondary: #D2F00F;
    --text: var(--txt, #cfcfcf);
    --border: var(--bd, #c0c0c0);
    --background: var(--bg, #1D1F21);
    font-size: min(calc(.75rem + 0.75vw), 16px);
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
    margin-top: 1em;
}

nav > a, nav > span {
    padding: 0.25em 0.75em;
}

nav > span {
    color: var(--border);
}

button.report, button.unreport, button.hide, button.show {
    background: transparent;
    border: 0px transparent;
    padding: 0px;
    margin: 0px;
    display: inline;
    box-sizing: border-box;
    font: inherit;
    color: inherit;
}

button.report:hover, button.unreport, button.hide:hover, button.show {
    opacity: 0.8;
    cursor: pointer;
}

.title-br { display: none; }

@media screen and (max-width: 470px) {
    header { text-align: center; }
    .title-br { display: initial; }
    .title-span { margin: 10px 0px; display: inline-block; }
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
        pub_display = publication
        try:
            pub_date = datetime.strptime(publication, "%Y-%m-%d")
            pub_display = pub_date.strftime("%d/%m/%Y")
        except ValueError:
            pass
        lines.append(
            f'\t\t\t\t\t<time datetime="{publication}">{pub_display}</time>'
        )
        lines.append("\t\t\t\t\t|")
        lines.append(
            f'\t\t\t\t\t<a class="domain" href="https://{domain}" target="_blank">{domain}</a> | '
        )
        lines.append(
            f'\t\t\t\t\t<button class="hide">esconder</button> | '
        )
        lines.append(
            f'\t\t\t\t\t<button class="report">reportar</button>'
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
        parts.append(f'\t\t\t<a href="{prev_file}">&larr; Voltar</a>')
    else:
        parts.append("\t\t\t<span>&larr; Voltar</span>")

    parts.append(f"\t\t\t<span>Página {current_page} de {total_pages}</span>")

    if current_page < total_pages:
        next_file = page_filename(current_page + 1)
        parts.append(f'\t\t\t<a href="{next_file}">Avançar &rarr;</a>')
    else:
        parts.append("\t\t\t<span>Avançar &rarr;</span>")

    parts.append("\t\t</nav>")
    return "\n".join(parts)


def render_page_skeleton(
    name: str,
    description: str,
    main_html: str,
) -> str:
    """Render the common HTML skeleton shared by all pages."""
    nonce = secrets.token_hex(16)
    now = datetime.now(timezone.utc)
    day = now.strftime("%A")
    dt_display = now.strftime("%d/%m/%Y %H:%M:%S")
    dt_rfc3339 = now.isoformat()

    return f"""\
<!DOCTYPE html>
<html lang="en" dir="ltr">

<head>
\t<meta charset="UTF-8">
\t<meta name="viewport" content="width=device-width, initial-scale=1">

\t<title>{escape(name)}</title>

\t<meta http-equiv="Content-Security-Policy" content="
\t\tdefault-src 'none';
\t\tconnect-src {BACKEND_URL};
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
\t\t<br class="title-br"/>
\t\t<span class="title-span">{escape(description)}</span>
\t</header>
\t<main>
{main_html}
\t</main>
\t<footer>
\t\t<p>Atualizado em:
\t\t\t<time id="update-at" datetime="{dt_rfc3339}">
\t\t\t\t{day}, {dt_display}
\t\t\t</time>
\t\t</p>
\t\t<p><a href="index.html">BR Crawl</a> | <a href="about.html">Sobre</a> | <a href="sources.html">Fontes</a></p>
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
<script type="module" nonce="{nonce}">
{JS}
</script>

</html>
"""


def render_page(
    items: list[dict],
    page_num: int,
    total_pages: int,
    start_index: int,
    name: str,
    description: str,
) -> str:
    """Render a full HTML page."""
    items_html = render_items_html(items, start_index)
    nav_html = render_nav(page_num, total_pages)
    main_html = f"{items_html}\n{nav_html}" if nav_html else items_html
    return render_page_skeleton(name, description, main_html)


_WARNING_RE = re.compile(
    r"^WARNING: fail to parse feed at (https?://\S+?):\s+(.+)$"
)


def parse_warnings(warnings_path: Path) -> dict[str, str]:
    """Parse a tinyfeed warnings log and return {url: error_description}."""
    failed: dict[str, str] = {}
    for line in warnings_path.read_text().splitlines():
        m = _WARNING_RE.match(line.strip())
        if m:
            failed[m.group(1)] = m.group(2)
    return failed


def render_sources_page(
    feed_urls: list[str],
    name: str,
    description: str,
    failed: dict[str, str] | None = None,
) -> str:
    """Render the sources.html page listing successful and failed feed URLs."""
    if failed is None:
        failed = {}

    failed_urls = set(failed.keys())
    ok_urls = [u for u in feed_urls if u not in failed_urls]

    lines: list[str] = []

    # Successful sources
    lines.append(f"\t\t<h2>Ativos ({len(ok_urls)})</h2>")
    lines.append("\t\t<ol>")
    for url in ok_urls:
        escaped_url = escape(url, quote=True)
        lines.append(
            f'\t\t\t<li><a href="{escaped_url}" target="_blank">{escaped_url}</a></li>'
        )
    lines.append("\t\t</ol>")

    # Failed sources
    if failed:
        lines.append(f"\t\t<h2>Inativos ({len(failed)})</h2>")
        lines.append("\t\t<ol>")
        for url, error in sorted(failed.items()):
            escaped_url = escape(url, quote=True)
            escaped_error = escape(error)
            lines.append(
                f'\t\t\t<li><a href="{escaped_url}" target="_blank">{escaped_url}</a>'
                f"<br><small>{escaped_error}</small></li>"
            )
        lines.append("\t\t</ol>")

    main_html = "\n".join(lines)
    return render_page_skeleton(f"Fontes | {name}", description, main_html)


def render_about_page(
    about_html: str,
    name: str,
    description: str,
) -> str:
    """Render the about.html page from raw HTML content."""
    main_html = f"\t\t{about_html}"
    return render_page_skeleton(f"Sobre | {name}", description, main_html)


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
    parser.add_argument(
        "-s",
        "--sources",
        default=None,
        help="Path to feeds.txt file listing feed URLs (one per line) for sources.html",
    )
    parser.add_argument(
        "-a",
        "--about",
        default=None,
        help="Path to about.txt file containing raw HTML content for about.html",
    )
    parser.add_argument(
        "-w",
        "--warnings",
        default=None,
        help="Path to tinyfeed warnings log for failed feed detection",
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

    failed: dict[str, str] = {}
    if args.warnings:
        warnings_path = Path(args.warnings)
        if warnings_path.exists():
            failed = parse_warnings(warnings_path)
            if failed:
                print(f"Detected {len(failed)} failed feed(s) from warnings log")

    if args.sources:
        sources_path = Path(args.sources)
        if not sources_path.exists():
            print(f"Error: sources file not found: {sources_path}", file=sys.stderr)
            sys.exit(1)
        feed_urls = [
            line.strip()
            for line in sources_path.read_text().splitlines()
            if line.strip()
        ]
        sources_html = render_sources_page(
            feed_urls, args.name, args.description, failed
        )
        sources_out = output_dir / "sources.html"
        sources_out.write_text(sources_html)
        ok_count = len(feed_urls) - len(set(feed_urls) & set(failed))
        print(
            f"Generated {sources_out} ({ok_count} active, {len(failed)} unreachable)"
        )

    if args.about:
        about_path = Path(args.about)
        if not about_path.exists():
            print(f"Error: about file not found: {about_path}", file=sys.stderr)
            sys.exit(1)
        about_content = about_path.read_text()
        about_html = render_about_page(about_content, args.name, args.description)
        about_out = output_dir / "about.html"
        about_out.write_text(about_html)
        print(f"Generated {about_out}")

    print(f"Done: {total_pages} page(s), {len(items)} items total")


if __name__ == "__main__":
    main()
