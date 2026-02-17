import scrapy
import re
import json
from datetime import datetime

import logging

from urllib.parse import urlparse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import SitemapSpider
import os
logging.getLogger('protego._protego').setLevel(logging.INFO)


class ExternalUrlsSpider(SitemapSpider):
    name = "external_urls"

    async def start(self):
        self.urls_file = getattr(self, "urls_file", None)
        if self.urls_file is None:
            raise scrapy.exceptions.CloseSpider("Missing urls_file argument")
        if not os.path.exists:
            raise scrapy.exceptions.CloseSpider(f"File <{self.urls_file}> not found")

        self.sitemap_urls = []
        self.crawled_at_by_domain = {}
        self.page_count_by_domain = {}
        self.limit_pages_by_domain = 150
        with open(self.urls_file, 'r') as f:
            for line in f.readlines():
                seed = json.loads(line)
                self.page_count_by_domain[seed['domain']] = 0
                self.crawled_at_by_domain[seed['domain']] = datetime.strptime(seed['crawled_at'], "%Y-%m-%d %H:%M:%S").date() if seed['crawled_at'] else None
                url = f"https://{seed['domain']}/sitemap.xml"
                self.sitemap_urls.append(url)
        async for item_or_request in super().start():
            yield item_or_request

    def sitemap_filter(self, entries):
        for entry in entries:
            # Each entry is a {"loc": "", "lastmod": ""} dictionary
            # lastmod seems to be either YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ
            loc = entry['loc']

            # skip common wordpress url patterns
            if "/tag/" in loc:
                return
            if "/category/" in loc:
                return

            domain = urlparse(entry['loc']).netloc

            if self.page_count_by_domain[domain] >= self.limit_pages_by_domain:
                return

            crawled_at = self.crawled_at_by_domain[domain]
            if 'lastmod' in entry and crawled_at is not None:
                mod_date = None
                try:
                    mod_date = datetime.strptime(entry["lastmod"], "%Y-%m-%d").date()
                except SyntaxError:
                    mod_date = datetime.strptime(entry["lastmod"], "%Y-%m-%dT%H:%M:%S%z").date()
                if mod_date >= crawled_at:
                    self.page_count_by_domain[domain] += 1
                    yield entry
            else:
                # if we have no metadata, always crawl
                self.page_count_by_domain[domain] += 1
                yield entry

    def parse(self, response):
        self.log(f"Scrapping URL {response.url}")
        parsed_url = urlparse(response.url)

        domain = parsed_url.netloc
        path = parsed_url.path

        link_extractor = LinkExtractor(unique=True, deny_domains=[domain])
        links = link_extractor.extract_links(response)
        yield {
            "blog_page": f"https://{domain}{path}",
            "blog_url": f"https://{domain}",
            "external_urls": [link.url for link in links]
        }
