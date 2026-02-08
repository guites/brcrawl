#!/usr/bin/env python3
"""Extract unique URLs from a .jsonl file's external_urls fields."""

import json
import sys


def parse_urls(jsonl_path: str):
    """Yield every external URL from the .jsonl file, one at a time."""
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            for url in record.get("external_urls", []):
                yield url.rstrip("/")


def unique(urls):
    """Yield only the first occurrence of each URL."""
    seen: set[str] = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            yield url


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input.jsonl>", file=sys.stderr)
        sys.exit(1)

    for url in unique(parse_urls(sys.argv[1])):
        print(url)


if __name__ == "__main__":
    main()
