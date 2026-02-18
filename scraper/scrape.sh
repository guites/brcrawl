#!/bin/bash

if [[ -z "$1" || ! -d "$1" ]]; then
    echo "Usage: ./scrape.sh <directory>"
    echo "<directory> is the path to a directory with a seeds.txt and blocklist.txt file, and where the program output will be saved."
    exit 1
fi

if [[ ! -f "$1/seeds.jsonl" || ! -f "$1/blocklist.txt" ]]; then
    echo "Please create the seeds.jsonl and blocklist.txt files"
    echo "See README.md for instructions"
    exit 1
fi

# 1. Gets all external URLs mentioned on existing blog posts
uv run scrapy crawl external_urls -a urls_file="$1/seeds.jsonl" -o "$1/external_urls.jsonl"

# TODO: handle repetion by www.

# 2. Flatten list of external urls and remove duplicate domains;
uv run unique_urls.py "$1/external_urls.jsonl" > "$1/unique_urls.txt"

# TODO: how do we filter out mastodon instances?
# TODO: use a separate list for filtering subdomains? ex. xxx.substack.com, xxx.tumblr.com, etc

# 3. Filter out unwanted domains and domains we have already indexed
uv run filter_urls.py "$1/unique_urls.txt" "$1/blocklist.txt" > "$1/filter_urls.txt"

# 4. Get RSS links for the external URLs
uv run scrapy crawl rss -a urls_file="$1/filter_urls.txt" -a no_rss="$1/no_rss.txt" -o "$1/rss.jsonl"

# 5. Determine whether website is written in portuguese
# TODO: check whether https://ai.google.dev/edge/mediapipe/solutions/text/language_detector/python would be a better solution
uv run scrapy crawl lang_detect -a urls_file="$1/rss.jsonl" -o "$1/lang_detect.jsonl"

# 6. Split between portuguese websites and other
jq -c '. | select(.lang == "pt")' "$1/lang_detect.jsonl" > "$1/lang_detect_pt.jsonl"
jq -c '. | select(.lang != "pt")' "$1/lang_detect.jsonl" > "$1/lang_detect_other.jsonl"

# 7. Query LLM (DeepSeek) on whether it's a personal blog or not
# currently we have a very rough prompt that excludes small publications,
# orgs and other blogs that would be welcome to our index
uv run scrapy crawl llm_classifier -a urls_file="$1/lang_detect_pt.jsonl" -o "$1/llm_classifier.jsonl"

# 8. Split based on LLM decision
jq -c '. | select(.personal_blog==true)' "$1/llm_classifier.jsonl" > "$1/llm_classifier_true.jsonl"
jq -c '. | select(.personal_blog==false)' "$1/llm_classifier.jsonl" > "$1/llm_classifier_false.jsonl"