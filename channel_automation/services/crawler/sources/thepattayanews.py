from typing import Optional

import json
import re

import aiohttp
import trafilatura
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_random_exponential

from channel_automation.models import NewsArticle

from ..utils import news_article_from_json

# Define headers and timeout as constants
timeout = aiohttp.ClientTimeout(total=15)
headers = {}


def extract_main_image(html_content: bytes) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    img_tag = soup.select_one("div.td-post-featured-image img")
    if img_tag and "src" in img_tag.attrs:
        return img_tag["src"]
    return None


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


class ThepattayaNewsCrawler:
    def __init__(self) -> None:
        pass

    async def crawl(self) -> list[NewsArticle]:
        print("Crawling Pattaya News")
        news_links = await self.crawl_news_links()
        print(f"Found {len(news_links)} news articles")
        print(news_links)
        extracted_articles = []
        for link in news_links:
            print(f"Extracting content from {link}")
            article = await self.extract_content(link)
            if article:
                extracted_articles.append(article)

        return extracted_articles

    async def crawl_news_links(self) -> list[str]:
        news_links = []
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = "https://thepattayanews.com/"
            html_content = await fetch_url(session, url, headers)
            links = self.extract_news_links(html_content)
            news_links.extend(links)

        return news_links

    def extract_news_links(self, html_content: str) -> list[str]:
        soup = BeautifulSoup(html_content, "html.parser")
        specific_news_links = []

        for div in soup.find_all("h3", {"class": re.compile("td-module-title")}):
            for a in div.find_all("a", href=True):
                specific_news_links.append(a["href"])

        return specific_news_links

    async def extract_content(self, url: str) -> Optional[NewsArticle]:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            downloaded = await fetch_article(session, url, headers)
            if downloaded is not None:
                try:
                    # Extracting main image URL
                    main_image_url = extract_main_image(downloaded)

                    extracted_data = trafilatura.extract(
                        downloaded,
                        include_comments=False,
                        with_metadata=True,
                        favor_precision=True,
                        deduplicate=True,
                        output_format="json",
                    )
                    if extracted_data is not None:
                        data = json.loads(extracted_data)
                        article = await news_article_from_json(data)

                        # Initialize images_url if it is None
                        if article.images_url is None:
                            article.images_url = []

                        # Adding main image URL to NewsArticle
                        if main_image_url:
                            article.images_url.append(main_image_url)

                        return article
                except Exception as e:
                    print(f"Error extracting content: {e}")
