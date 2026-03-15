#!/bin/bash
# We are testing whether truncating the home page of websites being sent to the llm for zero shot classification
# has a meaningful impact on page classification (personal blog true/false).
#
# Since we have the classification results from sending the full page text saved to llm_classifier.jsonl,
# this script adds a new key to the .jsonl objects in the format `"personal_blog_1000": false`.
# we can then use the personal_blog and personal_blog_1000 keys to derivate classification metrics

set -e
set -u

UV="/home/ubuntu/.local/bin/uv"
EXPERIMENTS_DIR="$PWD"
RUNS_DIR="$EXPERIMENTS_DIR/../runs"
SCRAPER_DIR="$EXPERIMENTS_DIR/../scraper"
declare -i PROCESSED_FILES=0
PROCESSED_FILES_NAMES=()

if [ ! "$#" -eq 2 ]; then
    echo "Usage: ./run_truncated_inference.sh <page_size_limit> <number_of_runs>";
    echo "  <page_size_limit> is how many characters from the page we send to the LLM"
    echo "  <number_of_runs> is how many llm_classifier.jsonl files we should process"
    exit 1
fi

TRUNCATE_SIZE="$1"
NUMBER_RUNS="$2"


if [[ "$EXPERIMENTS_DIR" != *"/experiments" ]]; then
    echo "Run script from brcrawl/experiments directory."
    exit 1
fi

echo "Truncating pages to $TRUNCATE_SIZE characters."
echo "Will run $NUMBER_RUNS time(s)."

shopt -s globstar

for dir in "$RUNS_DIR"/**/; do
    if [ "$PROCESSED_FILES" -ge "$NUMBER_RUNS" ]; then
        echo "Finished running $NUMBER_RUNS times."
        exit 0
    fi
    echo "---------------------------------------"
    echo "Entering directory: $dir"
    cd "$dir"

    input_file="$dir/llm_classifier.jsonl"
    output_file="$dir/llm_classifier_truncate_$TRUNCATE_SIZE.jsonl"

    if [ ! -f "$input_file" ]; then
        echo "Directory has no valid llm_classifier.jsonl file. Skipping..."
        cd - > /dev/null # Go back to the previous directory
        continue
    fi

    if [ ! -f "$output_file" ]; then
        echo "File <$output_file> not found. Running spider..."
        cd "$SCRAPER_DIR"
        "$UV" run scrapy crawl llm_classifier_truncate -a urls_file="$input_file" -a truncate_text="$TRUNCATE_SIZE" -o "$output_file"
        cd - > /dev/null # Go back to the previous directory
        PROCESSED_FILES=$((PROCESSED_FILES+1))
        PROCESSED_FILES_NAMES+="$input_file"
    else
        echo "File <$output_file> already exists. Skipping..."
    fi

    echo
    echo
    echo

    cd - > /dev/null # Go back to the previous directory
done

echo "Processed $PROCESSED_FILES."
printf "%s\\n" "${PROCESSED_FILES_NAMES[@]}"
