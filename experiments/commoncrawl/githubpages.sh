#!/bin/bash

set -u
set -e

if [ ! -f collinfo.json ]; then
    echo "collinfo.json not found. Fetching...";
    curl https://index.commoncrawl.org/collinfo.json > collinfo.json
fi

# check if collinfo.json has valid json
if ! jq . collinfo.json > /dev/null 2>&1; then
    echo "Couldn't parse collinfo.json information. Aborting."
    exit 1
fi

for crawl_id in $(jq -r ".[]|.id" collinfo.json); do
    # create crawl directory
    mkdir -p "$crawl_id"

    # get crawl information : number of pages
    if [ ! -f "$crawl_id/info.json" ]; then
        curl -s -S --retry 20 "https://index.commoncrawl.org/$crawl_id-index?url=*.github.io&output=json&showNumPages=true" > "$crawl_id/info.json"
    fi

    # check if the final retry generated valid json
    if ! jq . "$crawl_id/info.json" > /dev/null 2>&1; then
        echo "Couldn't parse $crawl_id information. Skipping."
        continue
    fi

    pages=$(jq .pages "$crawl_id/info.json")
    pages=$((pages+0))

    if [ "$pages" == 0 ]; then
        echo "Invalid pages for $crawl_id. Skipping."
        continue
    fi

    echo "Found $pages pages for $crawl_id"

    declare -i page=0

    while [ "$page" -lt "$pages" ]; do
        dl_path="$crawl_id/$page.json"
        if [ -f "$dl_path" ]; then
            # page already fetched, skip
            page=$((page+1))
            continue
        fi

        echo "Downloading $crawl_id - page $page"
        curl -s -S --retry 20 --http1.1 "https://index.commoncrawl.org/$crawl_id-index?url=*.github.io&output=json&page=$page" > "$dl_path"

        # the final json might have artifacts from previous errored retries
        if ! jq . "$dl_path" > /dev/null 2>&1; then
            echo "  > Error parsing $dl_path."
            continue
        fi
        
        page=$((page+1))
        # always sleep before next page download
        sleep 1
    done

    # echo "Concatenating downloaded pages json"
    # find "$crawl_id" -name "*.json" -type f -not -name "pages.json" -not -name "info.json" -print0 | xargs -0 cat > "$crawl_id/pages.json"

    # echo "Filtering unique domains"
    # jq -r '. | select(.languages // "" | contains("por")) | .url' "$crawl_id/pages.json" | sed -E 's#https?://([^/]+)/?.*#\1#' | sort -u > "$crawl_id/domains.txt"

    # cat "$crawl_id/domains.txt" >> githubpages.txt
done
