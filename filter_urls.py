#!/usr/bin/env python3
"""Filter URLs by removing entries matching a blocklist of domains."""

import sys
from urllib.parse import urlparse


def load_blocklist(blocklist_path: str) -> set[str]:
    """Load blocked domains from a text file (one domain per line)."""
    with open(blocklist_path) as f:
        return {line.strip() for line in f if line.strip()}


def filter_urls(urls_path: str, blocked_domains: set[str]):
    """Yield URLs whose domain is not in the blocklist."""
    with open(urls_path) as f:
        for line in f:
            url = line.strip()
            if not url:
                continue
            domain = urlparse(url).netloc
            if domain not in blocked_domains:
                yield url


def main():
    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} <urls.txt> <blocklist.txt>",
            file=sys.stderr,
        )
        sys.exit(1)

    urls_path, blocklist_path = sys.argv[1], sys.argv[2]
    blocked_domains = load_blocklist(blocklist_path)

    for url in filter_urls(urls_path, blocked_domains):
        print(url)


if __name__ == "__main__":
    main()
