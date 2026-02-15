#!/bin/bash
# Builds the html files for publishing brcrawl as a static website
set -e # exit on error
set -u # error on undefined variables


# Change according to your system installation
UV_EXECUTABLE="/home/ubuntu/.local/bin/uv"

if [ ! -f "$1" ]; then
    echo "Usage: ./build.sh feeds.txt"
    echo "feeds.txt is a list of website rss feed URLs (one per line)"
    exit 1
fi

split -d -l 50 "$1" feed_part

name="BR Crawl"
description="Diretório da smallweb brasileira"

: > warnings.log  # truncate/create the warnings log

for feed in "$PWD"/feed_part*; do
    if [[ "$feed" == *".json" ]]; then
        echo "Skipping $feed"
        continue
    fi
    echo "Processing $feed"
    cat "$feed" | docker run -v .:/app -i thebigroomxxl/tinyfeed -t feed.json.tmpl -L 1 -r 4 > "$feed.json" 2>> warnings.log
done

# Concatenate all JSON files, sort by publication date (YYYY-MM-DD) descending
jq -s 'add | sort_by(.publication) | reverse' "$PWD"/feed_part*.json > feeds.json

# Build paginated HTML pages from the merged JSON
SCRIPT_DIR="$(dirname "$0")"

"$UV_EXECUTABLE" run "$SCRIPT_DIR/build_html.py" feeds.json -o . -n "$name" -d "$description" -s "$1" -a "$SCRIPT_DIR/about.txt" -w warnings.log

# Clean up intermediate files
rm -f "$PWD"/feed_part* warnings.log
