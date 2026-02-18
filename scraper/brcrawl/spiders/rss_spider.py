import scrapy

import logging
from urllib.parse import urlparse, urljoin

logging.getLogger('protego._protego').setLevel(logging.INFO)

RSS_SUFFIXES = [
    '/feed', '/feed/', '/rss', '/atom', '/feed.xml',
    '/index.atom', '/index.rss', '/index.xml', '/atom.xml', '/rss.xml',
    '/.rss', '/blog/index.xml', '/blog/index.rss', '/blog/feed.xml',
]


class RssSpider(scrapy.Spider):
    name = "rss"

    async def start(self):
        self.urls_file = getattr(self, "urls_file", None)
        if self.urls_file is None:
            raise scrapy.exceptions.CloseSpider("Missing urls_file argument")

        self.no_rss = getattr(self, "no_rss", None)
        if self.no_rss is not None:
            try:
                with open(self.no_rss, "a", encoding='utf-8') as nr:
                    nr.write("\n")
            except Exception:
                raise scrapy.exceptions.CloseSpider(f"Cannot write to no_rss file: {self.no_rss}")

        with open(self.urls_file, 'r') as f:
            for line in f:
                url = line.strip().strip('/')
                if not url:
                    continue
                if url.startswith('//'):
                    url = 'https:' + url
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    cb_kwargs={"base_url": self._base_url(url)},
                    errback=self.handle_error,
                )

    def _base_url(self, url):
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _domain(self, url):
        parsed = urlparse(url)
        return parsed.netloc

    def parse(self, response, base_url):
        rss_links = response.css('link[rel="alternate"]')
        if rss_links:
            href = rss_links[0].attrib.get("href")
            if href:
                rss_url = urljoin(base_url, href)
                self.logger.info(f"Found RSS link for {response.url}: {rss_url}")
                yield {"url": response.url, "rss_url": rss_url, "domain": self._domain(response.url)}
                return

        # No <link rel="alternate"> found — try common RSS suffixes
        suffix_url = base_url.rstrip('/') + RSS_SUFFIXES[0]
        yield scrapy.Request(
            url=suffix_url,
            callback=self.parse_suffix,
            cb_kwargs={
                "original_url": response.url,
                "base_url": base_url,
                "suffix_index": 0,
            },
            errback=self.handle_suffix_error,
            dont_filter=True,
        )

    def parse_suffix(self, response, original_url, base_url, suffix_index):
        rss_url = response.url

        self.logger.info(f"Found RSS link for {original_url}: {rss_url}")
        yield {"url": original_url, "rss_url": rss_url, "domain": self._domain(original_url)}

    def handle_suffix_error(self, failure):
        request = failure.request
        original_url = request.cb_kwargs["original_url"]
        base_url = request.cb_kwargs["base_url"]
        suffix_index = request.cb_kwargs["suffix_index"]

        next_index = suffix_index + 1
        if next_index < len(RSS_SUFFIXES):
            suffix_url = base_url.rstrip('/') + RSS_SUFFIXES[next_index]
            yield scrapy.Request(
                url=suffix_url,
                callback=self.parse_suffix,
                cb_kwargs={
                    "original_url": original_url,
                    "base_url": base_url,
                    "suffix_index": next_index,
                },
                errback=self.handle_suffix_error,
                dont_filter=True,
            )
        else:
            self.logger.warning(f"No RSS link found for {original_url}")
            if self.no_rss is not None:
                with open(self.no_rss, "a", encoding='utf-8') as f:
                    f.write(f"{self._domain(original_url)}\n")

    def handle_error(self, failure):
        self.logger.error(f"Error fetching {failure.request.url}: {failure.value}")
