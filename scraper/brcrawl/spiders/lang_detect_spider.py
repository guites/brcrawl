import scrapy
import re
import jsonlines
import logging
from langdetect import detect
import time
from bs4 import BeautifulSoup

logging.getLogger('protego._protego').setLevel(logging.INFO)


class LangDetectSpider(scrapy.Spider):
    name = "lang_detect"

    async def start(self):
        self.urls_file = getattr(self, "urls_file", None)
        if self.urls_file is None:
            raise scrapy.exceptions.CloseSpider("Missing urls_file argument")
        with jsonlines.open(self.urls_file) as reader:
            for obj in reader:
                url = obj.get("url")
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    cb_kwargs={"obj": obj},
                )


    def parse(self, response, obj):
        page_body = response.css("body")
        page_main = page_body.css("main")
        if page_main:
            soup = BeautifulSoup(page_main.get(), 'lxml')
        else:
            soup = BeautifulSoup(page_body.get(), 'lxml')
        page_text = soup.get_text().strip()
        self.logger.debug(page_text[:50])
        start_time = time.perf_counter()
        obj['lang'] = detect(page_text)
        elapsed_time = time.perf_counter() - start_time
        self.logger.info(f"Lang detected in {elapsed_time:.2f}s")
        yield obj