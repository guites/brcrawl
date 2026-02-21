#!/bin/bash
set -e
set -u

# Orchestrates processes to crawl verified blogs and find
# links to new blogs written in portuguese.
# This is the glue between the backend/ and scraper/ subprojects.
# The database at backend/ manages which blogs where crawled and when
# and keeps a status for every blog (whether they have been verified,
# just been crawled, blocked, etc);

# Creates new run directory
# adapted from https://stackoverflow.com/a/2793856
function get_dir() {
    local dir_name
    local dir_path
    dir_name=$(cat /dev/urandom | tr -cd 'a-f0-9' | head -c 16)
    dir_path="$1/runs/$dir_name"
    if [[ -d "$dir_path" ]]; then
        echo $(get_dir "$1")
    else
        echo "$dir_path"
    fi
}

# Wraps a command call in `docker exec`
# if the global IS_DOCKERIZED is set
# expects $1 to be a command
function run_cmd() {
    if [[ "$IS_DOCKERIZED" -eq 1 ]]; then
        docker exec brcrawl_app bash -c "$@"
    else
        eval "$*"
    fi
}

# Parse boolean flags
if [[ "$*" == *"--dockerized"* ]]; then
    IS_DOCKERIZED=1
else
    IS_DOCKERIZED=0
fi

ROOT_DIR=$(run_cmd "pwd")
BACKEND_DIR="$PWD/backend"
SCRAPER_DIR="$PWD/scraper"

DIR_PATH=$(get_dir "$ROOT_DIR")
run_cmd "mkdir -p \"$DIR_PATH\""

# This is necessary when running --dockerized,
# becomes redundant when running locally
DIR_PATH_SCRAPE=$(pwd)${DIR_PATH#${ROOT_DIR}}

# Generates the seed URLs for crawling
cd "$BACKEND_DIR"
run_cmd "uv run flask crawl-feeds --limit 25 --output \"$DIR_PATH/seeds.jsonl\" --mark-crawled"

# Creates the blocklist, composed of known unwanted domains and all
# domains we have already registered to avoid unnecessary http requests
run_cmd "uv run flask known-domains --output \"$DIR_PATH/blocklist.txt\""

# Starts the web crawling pipeline
cd "$SCRAPER_DIR"
./scrape.sh "$DIR_PATH_SCRAPE"

cd "$BACKEND_DIR"

# Import domains that have no valid feed url to the database blocklist
run_cmd "uv run flask import-blocklist \"$DIR_PATH/no_rss.txt\""

# Import feeds that are not in portuguese as "blocked" to the database
run_cmd "uv run flask import-feeds \"$DIR_PATH/lang_detect_other.jsonl\" --feed-status=\"blocked\" --output \"$DIR_PATH/import_feeds_lang_detect_other.json\" --descr=\"lang_detect_other\""

# Import feeds that are **not** personal_blogs as "blocked" to the database
run_cmd "uv run flask import-feeds \"$DIR_PATH/llm_classifier_false.jsonl\" --feed-status=\"blocked\" --output \"$DIR_PATH/import_feeds_llm_classifier_false.json\" --descr=\"llm_classifier_false\""

# Import feeds considered personal_blogs as "crawled" to the database
run_cmd "uv run flask import-feeds \"$DIR_PATH/llm_classifier_true.jsonl\" --feed-status=\"crawled\" --output \"$DIR_PATH/import_feeds_llm_classifier_true.json\""
