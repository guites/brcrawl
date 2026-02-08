#!/bin/bash

if [[ ! -f "urls.txt" || ! -f "blocklist.txt" ]]; then
    echo "Please create the urls.txt and blocklist.txt files"
    echo "See README.md for instructions"
    exit 1
fi

# 1. Gets all external URLs mentioned on existing blog posts
uv run scrapy crawl external_urls -a urls_file=urls.txt -o external_urls.jsonl

# 2. Flatten list of external urls and remove duplicate domains
uv run unique_urls.py external_urls.jsonl > unique_urls.txt

# TODO: how do we filter out mastodon instances?
# TODO: use a separate list for filtering subdomains? ex. xxx.substack.com
# 3. Filter out known unwanted domains and URLs
uv run filter_urls.py unique_urls.txt blocklist.txt > filtered_urls.txt

# 4. Get RSS links for the external URLs
uv run scrapy crawl rss -a urls_file=filtered_urls.txt -o rss.jsonl

# 5. Determine whether website is written in portuguese
# TODO: https://pypi.org/project/langdetect or
# https://ai.google.dev/edge/mediapipe/solutions/text/language_detector/python
