#!/bin/bash

if [[ -z "$1" || ! -d "$1" ]]; then
    echo "Usage: ./brcrawl.sh <directory>"
    echo "<directory> is the path to a directory with a urls.txt and blocklist.txt file, and where the program output will be saved."
    exit 1
fi

if [[ ! -f "$1/urls.txt" || ! -f "$1/blocklist.txt" ]]; then
    echo "Please create the urls.txt and blocklist.txt files"
    echo "See README.md for instructions"
    exit 1
fi

# 1. Gets all external URLs mentioned on existing blog posts
uv run scrapy crawl external_urls -a urls_file="$1/urls.txt" -o "$1/external_urls.jsonl"

# 2. Flatten list of external urls and remove duplicate domains
uv run unique_urls.py "$1/external_urls.jsonl" > "$1/unique_urls.txt"

# TODO: how do we filter out mastodon instances?
# TODO: use a separate list for filtering subdomains? ex. xxx.substack.com
# 3. Filter out known unwanted domains and URLs
uv run filter_urls.py "$1/unique_urls.txt" "$1/blocklist.txt" > "$1/filtered_urls.txt"

# 4. Get RSS links for the external URLs
uv run scrapy crawl rss -a urls_file="$1/filtered_urls.txt" -o "$1/rss.jsonl"

# 5. Determine whether website is written in portuguese
# TODO: https://pypi.org/project/langdetect or
# https://ai.google.dev/edge/mediapipe/solutions/text/language_detector/python
