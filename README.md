# BR Crawl

This projects aims to crawl and index existing indieweb/smallweb adjacent blogs by brazilian authors.

It is composed of different crawlers, each with a separate objective.

## Installation

The project was created using [uv](https://docs.astral.sh/uv).

With `uv` installed:

```
uv sync
```

## BearblogDiscoverSpider

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
uv run scrapy crawl bearblog_discover -o second_run.jsonl -a latest="//yaletown.observer/youve-got-to-believe-you-hear-me"
```

Get the URL for the latest flag by looking at the first line of your last generated .jsonl.

Get latest post by each blog:

```
cat first_run.jsonl second_run.jsonl > input.jsonl

jq -n '
  reduce inputs as $item
    ({};
     .[$item.blog_url] as $existing
     | if $existing == null
         or $item.published_at > $existing.published_at
       then
         .[$item.blog_url] = $item
       else
         .
       end
    )
  | [ .[] ]                     # turn the map into a JSON array
  | sort_by(.published_at)      # oldest → newest
  | reverse                     # newest → oldest
' input.jsonl > latest-per-blog.json
```