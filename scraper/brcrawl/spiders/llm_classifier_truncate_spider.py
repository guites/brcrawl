import scrapy
from scrapy.exceptions import CloseSpider
import jsonlines
import logging
import time
from bs4 import BeautifulSoup
import os
from llama_index.llms.deepseek import DeepSeek
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage
from llama_index.core.bridge.pydantic import BaseModel
from dotenv import load_dotenv
import re

load_dotenv()

logging.getLogger('protego._protego').setLevel(logging.INFO)

DEEPSEEK_API_KEY = os.environ['DEEPSEEK_API_KEY']

class Website(BaseModel):
    personal_blog: bool

class LLMClassifierTruncateSpider(scrapy.Spider):
    name = "llm_classifier_truncate"

    async def start(self):
        self.urls_file = getattr(self, "urls_file", None)
        if self.urls_file is None:
            raise CloseSpider("Missing urls_file argument")
        self.llm = DeepSeek(model='deepseek-chat', api_key=DEEPSEEK_API_KEY)
        self.truncate_text = getattr(self, 'truncate_text', None)
        if self.truncate_text is not None:
            self.truncate_text = int(self.truncate_text)
        Settings.llm = self.llm
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
            soup = BeautifulSoup(page_main.get(), "lxml")
        else:
            soup = BeautifulSoup(page_body.get(), "lxml")
        page_text = soup.get_text().strip()
        page_text = re.sub(r"\s+", " ", page_text).strip()
        if self.truncate_text:
            page_text = page_text[: self.truncate_text]
        self.logger.debug("Page text length: %s", len(page_text))
        start_time = time.perf_counter()
        sllm = self.llm.as_structured_llm(Website).chat(
            [
                ChatMessage(
                    role="system",
                    content=f"""
                    Classifique o texto abaixo extraído de um website brasileiro. O objetivo é definir se o website se trata de um BLOG PESSOAL. Caso seja um blog pessoal, você deve classificá-lo como True. Em caso negativo, você deve classificá-lo como False.

                    --- Início do texto ---
                    {page_text}
                    --- Fim do texto ---

                    Classes: True, False
                    """,
                )
            ]
        )
        model_output = sllm.raw
        if self.truncate_text:
            obj[f"personal_blog_{self.truncate_text}"] = model_output.personal_blog
        else:
            obj["personal_blog"] = model_output.personal_blog
        elapsed_time = time.perf_counter() - start_time
        self.logger.info(f"Site classified in {elapsed_time:.2f}s")
        yield obj
