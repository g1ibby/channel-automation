from typing import List, Optional

import json

import aiohttp
import trafilatura
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_random_exponential

from channel_automation.models import NewsArticle

from ..utils import news_article_from_json

# Define headers and timeout as constants
timeout = aiohttp.ClientTimeout(total=15)
headers = {}


@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, min=3, max=30),
)
async def fetch_url(session, url, headers):
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.text()
        else:
            print(f"Received status code {response.status}")
            return None


@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, min=3, max=30),
)
async def fetch_article(session, url, headers):
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.read()
        else:
            print(f"Received status code {response.status}")
            return None


def extract_main_image(html_content: bytes) -> Optional[str]:
    soup = BeautifulSoup(html_content, "html.parser")

    figure_tag = soup.select_one("div.wp-block-image figure.aligncenter a")
    if figure_tag and "href" in figure_tag.attrs:
        return figure_tag["href"]
    return None


class ClubbingThailandCrawler:
    def __init__(self) -> None:
        self.base_url = "https://clubbingthailand.com/"

    async def crawl(self) -> list[NewsArticle]:
        print("Crawling Clubbing Thailand for news articles.")
        news_links = await self.crawl_news_links()
        print(f"Found {len(news_links)} news articles")
        extracted_articles = []
        for link in news_links:
            print(f"Extracting content from {link}")
            article = await self.extract_content(link)
            if article:
                extracted_articles.append(article)
        return extracted_articles

    async def crawl_news_links(self) -> list[str]:
        filtered_news_links = []
        async with aiohttp.ClientSession(timeout=timeout) as session:
            html_content = await fetch_url(session, self.base_url, headers)
            filtered_news_links = self.extract_news_links(html_content)
        return filtered_news_links

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        news_links = []
        if not html_content:
            return news_links
        soup = BeautifulSoup(html_content, "html.parser")
        for item in soup.select(".pt-cv-content-item"):
            link = item.select_one("a.pt-cv-href-thumbnail")
            if link:
                news_links.append(link["href"])
        return news_links

    async def extract_content(self, url: str) -> Optional[NewsArticle]:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            downloaded = await fetch_article(session, url, headers)
            if downloaded:
                main_image_url = extract_main_image(downloaded)
                extracted_data = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    with_metadata=True,
                    favor_precision=True,
                    deduplicate=True,
                    output_format="json",
                )
                if extracted_data:
                    data = json.loads(extracted_data)
                    article = await news_article_from_json(data)
                    # Initialize images_url if it is None
                    if article.images_url is None:
                        article.images_url = []

                    # Adding main image URL to NewsArticle
                    if main_image_url:
                        article.images_url.append(main_image_url)
                    return article
