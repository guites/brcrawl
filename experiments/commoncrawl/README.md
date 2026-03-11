# Using the Common Crawl corpus

The [Common Crawl](https://commoncrawl.org/overview) project exposes a public json API which allows us to filter existing crawls by both snapshot and domain.

As far as I can tell each crawl seems to contain a unique batch of URLs, with a maximum of ~20% overlap ([source: crawloverlap](https://commoncrawl.github.io/cc-crawl-statistics/plots/crawloverlap)), so for every available crawl we'll go over all result pages.

Start by listing existing crawls:

```
$ curl https://index.commoncrawl.org/collinfo.json > collinfo.json
$ jq --raw-output ".[] | .id" collinfo.json | wc -l
121
```

There are 121 crawls! Let's check how many pages they have for our *.github.io filter:

```
$ curl "https://index.commoncrawl.org/CC-MAIN-2025-21-index?url=*.github.io&showNumPages=true"
{"pages": 33, "pageSize": 5, "blocks": 164}

$ curl "https://index.commoncrawl.org/CC-MAIN-2026-08-index?url=*.github.io&showNumPages=true"
{"pages": 30, "pageSize": 5, "blocks": 148}

$ curl "https://index.commoncrawl.org/CC-MAIN-2025-47-index?url=*.github.io&showNumPages=true"
{"pages": 29, "pageSize": 5, "blocks": 141}
```

Let's say each crawl has ~30 pages. 

```
$ curl "https://index.commoncrawl.org/CC-MAIN-2025-47-index?url=*.github.io&output=json&page=0" > CC-MAIN-2025-47-page-0.json
$ jq .url CC-MAIN-2025-47-page-0.json  | wc -l
14801
```

But there are multiple URLs for the same domain:

```
"https://0fajarpurnama0.github.io/cv/"
"https://0fajarpurnama0.github.io/deals/"
"https://0fajarpurnama0.github.io/doctoral/2020/07/25/student-thought-contribute-sdg.html"
"https://0fajarpurnama0.github.io/doctoral/2020/07/26/material-exploration-discovery-design"
"https://0fajarpurnama0.github.io/fiction/2020/01/01/dream-forcefully-reborn-as-girl.html"
"https://0fajarpurnama0.github.io/finance/2020/02/24/global-financial-system-and-crisis.html"
"https://0fajarpurnama0.github.io/finance/2020/02/24/towards-financial-freedom.html"
"https://0fajarpurnama0.github.io/internet/2020/02/24/bypass-censorship-by-dns.html"
"https://0fajarpurnama0.github.io/internet/2020/02/24/bypass-censorship-by-proxy.html"
```

They can be flattened using regex and `sort`:

```
$ jq -r '.url' CC-MAIN-2025-47-page-0.json | sed -E 's#https?://([^/]+)/?.*#\1#' | sort -u | wc -l
2058
```

Recent crawls (2018 onwards) have language annotations done via Compact Language Detector 2, which includes portuguese ([source](https://commoncrawl.org/blog/web-languages-needing-review-by-native-speakers)).

There doesnt seem to be a way to filter during the API request, so we can use `jq` to select urls that contain "por" as their main language.

```
$ jq -r '. | select(.languages // "" | contains("por")) | .url' CC-MAIN-2025-47-page-0.json | sed -E 's#https?://([^/]+)/?.*#\1#' | sort -u
4d-jp.github.io
91anwanj.github.io
91sdasijiann.github.io
91shipingg.github.io
abcd-community.github.io
abjur.github.io
ac3lab.github.io
adonispeng.github.io
a-fisalis.github.io
aguios.github.io
ail-mo-leti-cep.github.io
aiqingdd.github.io
aiyumi.github.io
alexandrehtrb.github.io
``` 

A much smaller result set (as expected) but still something that can grow to a noticiable size given the amount of pages and crawls (121 crawls * 30 pages * 14 unique domains ≈ 50k websites!).

A script automating the download of all results from all crawls can be found at [githubpages.sh](./githubpages.sh).

The [concat_results.sh](./concat_results.sh) script validates the generated json and compiles the resulting domains to a file.

## Results

A run over 9 crawls (from 2025-26 to 2026-04) resulted in 1108 domains that fit our criteria.

## Limitations / next steps

Usage of the Common Crawl API is restricted by a rather severe rate limit, and even curls default exponential backoff isn't enough to prevent getting temporarily banned. A more exaustive research would involve downloading the CC dataset from S3 as shards, which I considered infeasible given my current setup.

Another problem is that multiple blogs are not hosted at the root github subdomain. For example `user.github.io` may return a 404 but there could still be a blog at `user.github.io/myblog`. The current implementation considers only "top level" blogs.
