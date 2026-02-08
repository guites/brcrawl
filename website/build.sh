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
