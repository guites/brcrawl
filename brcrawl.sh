#!/bin/bash

# 1. Gets all external URLs mentioned on existing blog posts
uv run scrapy crawl external_urls -a urls_file=urls.txt -o 1.jsonl

# 2. Flatten list of external urls and remove duplicates
uv run unique_urls.py external.jsonl > 2.txt

# TODO: how do we filter out mastodon instances?
# 3. Filter out known unwanted domains and URLs
# get a count of most common domains with
# python -c "from collections import Counter; from urllib.parse import urlparse; print('\n'.join(f'{c} {d}' for d, c in Counter(urlparse(l.strip()).netloc for l in open('3.txt') if l.strip()).most_common(50)))"
uv run filter_urls.py 2.txt blocklist.txt > 3.txt

# 4. Get all RSS links from the external URLs
uv run scrapy crawl rss -a urls_file=3.txt -o 4.jsonl

# 5. Crawl RSS and download a few sample pages
uv run scrapy crawl rss_crawler -a urls_file=rss_links.txt -o rss_posts.jsonl

# 6. Determine whether website is written in portuguese
# TODO: https://github.com/thomasthiebaud/spacy-fastlang
