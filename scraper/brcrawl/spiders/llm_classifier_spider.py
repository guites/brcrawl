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

class LLMClassifierSpider(scrapy.Spider):
    name = "llm_classifier"

    async def start(self):
        self.urls_file = getattr(self, "urls_file", None)
        if self.urls_file is None:
            raise CloseSpider("Missing urls_file argument")
        self.llm = DeepSeek(model='deepseek-chat', api_key=DEEPSEEK_API_KEY)
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
            soup = BeautifulSoup(page_main.get(), 'lxml')
        else:
            soup = BeautifulSoup(page_body.get(), 'lxml')
        page_text = soup.get_text().strip()
        page_text = re.sub(r'\s+', ' ', page_text).strip()
        self.logger.debug(page_text[:50])
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
                    """
                )
            ])
        model_output = sllm.raw
        obj['personal_blog'] = model_output.personal_blog
        elapsed_time = time.perf_counter() - start_time
        self.logger.info(f"Site classified in {elapsed_time:.2f}s")
        yield obj