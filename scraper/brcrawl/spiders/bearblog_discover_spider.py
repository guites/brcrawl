import scrapy
import re

import logging

logging.getLogger('protego._protego').setLevel(logging.INFO)


class BearblogDiscoverSpider(scrapy.Spider):
    name = "bearblog_discover"

    async def start(self):

        self.latest = getattr(self, "latest", None)
        self.cookies = {'lang': 'pt'}
        urls = [
            "https://bearblog.dev/discover/?page=0&newest=true",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, cookies=self.cookies)


    def parse(self, response):
        page_num = re.findall(r"\?page=(.+)\&", response.url)[0]
        self.log(f"Scrapped page {page_num}")

        for post in response.css('ul.discover-posts > li'):
            post_url = post.css('div a::attr(href)')[0].get()
            if self.latest is not None:
                if self.latest == post_url:
                    raise scrapy.exceptions.CloseSpider("Reached latest saved post. Exiting.")
            yield {
                "blog_url": post.css('div a::text')[1].get(),
                "post_url": post_url,
                "published_at": post.css('div > small > small::attr(title)')[0].get()
            }

        pagination = response.css('ul.discover-posts + p > a::attr(href)')
        if pagination is not None:
            # scrapy automatically drops repeated urls
            for pagination_btn in pagination:
                pagination_url = pagination_btn.get()
                next_page = response.urljoin(pagination_url)
                yield scrapy.Request(next_page, callback=self.parse, cookies=self.cookies)
