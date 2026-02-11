# Scraper | BR Crawl

Crawl and index existing indieweb/smallweb blogs by brazilian authors.

It is composed of different crawlers, each with a separate objective.

## Installation

The project was created using [uv](https://docs.astral.sh/uv).

With `uv` installed:

```
uv sync
```

## Usage

The pipeline is described at `brcrawl.sh`.

In order to run the script you will need two files:

- urls.txt: list of initial blogs for crawling. One blog URL per line.
- blocklist.txt: list of domains that you want to exclude from the pipeline. One domain per line.

There are two example files that you can use as a starting point:

```
cp example.urls.txt urls.txt
cp example.blocklist.txt blocklist.txt
```

## BearblogDiscoverSpider

**This is not part of the pipeline, but was used to generate the starting `urls.txt` for the project.**

Crawls the bearblog discovery feed filtering by &newest=true with a lang=pt cookie.

The objective is that, once you run it through all existing pages, you will have a .jsonl file with all portuguese (hopefully brasilian) bearblog posts.

After running through the full scrapping process, you can use the `latest` flag to only run until you find the latest (newest?) post from the last run. This avoids overloading their server.

### Usage

First usage:

```
uv run scrapy crawl bearblog_discover -O first_run.jsonl
```

Posterior runs:

```
uv run scrapy crawl bearblog_discover -o second_run.jsonl -a latest="https://yaletown.observer/youve-got-to-believe-you-hear-me"
```

Get the list of unique blogs urls:

```
cat first_run.jsonl second_run.jsonl | jq -r .blog_url | sort -u > bearblog-urls.txt
```
