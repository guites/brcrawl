#!/bin/bash

# Builds the html files for publishing brcrawl as a static website

if [ ! -f "$1" ]; then
    echo "Usage: ./build.sh feeds.txt"
    echo "feeds.txt is a list of website rss feed URLs (one per line)"
    exit 1
fi

split -d -l 50 "$1" feed_part

name="BR Crawl"
description="Diretório da smallweb brasileira"

for feed in "$PWD"/feed_part*; do
    # TODO: save errors/warnings to a separate file for analysis
    cat "$feed" | docker run -v .:/app -i thebigroomxxl/tinyfeed -t feed.json.tmpl -L 1 -r 4 > "$feed.json"
done

# Concatenate all JSON files, sort by publication date (YYYY-MM-DD) descending
jq -s 'add | sort_by(.publication) | reverse' "$PWD"/feed_part*.json > feeds.json

# Build paginated HTML pages from the merged JSON
uv run "$(dirname "$0")/build_html.py" feeds.json -o . -n "$name" -d "$description"

# Clean up intermediate files
rm -f "$PWD"/feed_part*
