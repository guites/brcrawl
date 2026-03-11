#!/bin/bash

set -u
set -e

CONCAT_JSON="pages.json"
DOMAINS_TXT="domains.txt"

# Wipe previous results
echo -n "" > "$CONCAT_JSON"
echo -n "" > "$DOMAINS_TXT"

echo "Concatenating downloaded pages json"
find ./CC-MAIN-* -name "*.json" -type f -not -name "$CONCAT_JSON" -not -name "info.json" -print0 | \
    while IFS= read -r -d '' file; do
        if ! jq . "$file" > /dev/null 2>&1; then
            echo "Invalid json for file <$file>. Skipping..."
        else
            cat "$file" >> "$CONCAT_JSON"
        fi
    done

echo "Filtering unique domains"
jq -r '. | select(.languages // "" | contains("por")) | .url' "pages.json" | sed -E 's#https?://([^/]+)/?.*#\1#' | sort -u > "$DOMAINS_TXT"

NUM_DOMAINS=$(wc -l < "$DOMAINS_TXT")
echo "Found $NUM_DOMAINS unique domains"