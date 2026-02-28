#!/bin/bash
set -e
set -u

shopt -s globstar

ROOT_DIR="$PWD"
RUNS_DIR="$ROOT_DIR/runs"


if [ "$#" -eq 0 ]; then
    echo "Usage: ./llm_truncate.sh <page_size_limit>";
    exit 1
fi

TRUNCATE_SIZE="$1"

echo "Truncating pages to $TRUNCATE_SIZE characters."

for dir in "$RUNS_DIR"/**/; do
    echo "Entering directory: $dir"
    cd "$dir"

    output_file_true="$dir/llm_classifier_true_truncate_$TRUNCATE_SIZE.jsonl"
    output_file_false="$dir/llm_classifier_false_truncate_$TRUNCATE_SIZE.jsonl"
    if [ ! -f "$output_file_true" ]; then
        echo "File <$output_file_true> not found. Running spider..."
    fi
    if [ ! -f "$output_file_false" ]; then
        echo "File <$output_file_false> not found. Running spider..."
    fi
    uv run scrapy crawl llm_classifier -a urls_file="$RUNS_DIR/llm_classifier_true.jsonl" -a truncate_text=1000 -o "$output_file_true"
    uv run scrapy crawl llm_classifier -a urls_file="$RUNS_DIR/llm_classifier_false.jsonl" -a truncate_text=1000 -o "$output_file_false"
    cd - > /dev/null # Go back to the previous directory
done
