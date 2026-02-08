import scrapy
import re

import logging

from urllib.parse import urlparse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import SitemapSpider

logging.getLogger('protego._protego').setLevel(logging.INFO)


class ExternalUrlsSpider(SitemapSpider):
    name = "external_urls"

    async def start(self):

        self.urls_file = getattr(self, "urls_file", None)
        self.sitemap_urls = []
        with open(self.urls_file, 'r') as f:
            for line in f.readlines():
                url = line.strip().strip('/')
                if url.startswith('//'):
                    url = 'https:' + url
                url = url + '/sitemap.xml'
                self.sitemap_urls.append(url)
        async for item_or_request in super().start():
            yield item_or_request


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
