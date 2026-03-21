#!/bin/bash
# Uses the output from truncated_llm.sh to create a .csv file with columns
# URL , personal_blog , personal_blog_1000

set -e
set -u

if [ ! "$#" -eq 2 ]; then
    echo "Usage: ./generate_truncated_dataset.sh <page_size_limit> <output_file>";
    echo "  <page_size_limit> is how many characters from the page we send to the LLM"
    echo "  <output_file> where should the dataset csv be saved to (absolute path)"
    exit 1
fi

EXPERIMENTS_DIR="$PWD"
RUNS_DIR="$EXPERIMENTS_DIR/../runs"
TRUNCATE_SIZE="$1"
OUTPUT_FILE="$2"

if ! touch "$OUTPUT_FILE"; then
    echo "'$OUTPUT_FILE' is not writable."
    exit 1
fi

echo "url,personal_blog,personal_blog_$TRUNCATE_SIZE" > "$OUTPUT_FILE"

if [[ "$EXPERIMENTS_DIR" != *"/experiments" ]]; then
    echo "Run script from brcrawl/experiments directory."
    exit 1
fi

shopt -s globstar

for dir in "$RUNS_DIR"/**/; do
    cd "$dir"

    input_file="$dir/llm_classifier_truncate_$TRUNCATE_SIZE.jsonl"

    if [ ! -f "$input_file" ]; then
        cd - > /dev/null # Go back to the previous directory
        continue
    fi

    echo "Found $input_file. Processing..."
    # parse the .jsonl file and grab necessary columns
    jq --raw-output '. | [.url,.personal_blog,.personal_blog_1000] | @csv' "$input_file" >> "$OUTPUT_FILE"

    cd - > /dev/null # Go back to the previous directory
done
