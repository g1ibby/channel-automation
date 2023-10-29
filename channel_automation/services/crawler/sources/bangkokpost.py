from typing import Optional

import json

import aiohttp
import trafilatura
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_random_exponential

from channel_automation.models import NewsArticle

from ..utils import news_article_from_json

timeout = aiohttp.ClientTimeout(total=15)


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


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "X-Requested-With": "XMLHttpRequest",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": "https://www.bangkokpost.com/life/travel",
    "Cookie": "is_pdpa=1; bkp_survey=1; is_gdpr=1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


class BangkokpostCrawler:
    def __init__(self) -> None:
        pass

    async def crawl(self) -> list[NewsArticle]:
        print("Crawling Bangkok Post")
        news_links = await self.crawl_news_links()
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
            for page in range(1, 2):
                url = f"https://www.bangkokpost.com/v3/list_content/life/travel?page={page}"
                html_content = await fetch_url(session, url, headers)
                lnks = self.extract_news_links(html_content)
                news_links.extend(lnks)

        return news_links

    def extract_news_links(self, html_content):
        # Initialize a BeautifulSoup object
        soup = BeautifulSoup(html_content, "html.parser")

        # Initialize an empty list to store the news links
        specific_news_links = []

        # Find and loop through each news item
        for news_item in soup.find_all("div", class_="news--list boxnews-horizon"):
            link_tag = news_item.find("figure").find("a", href=True)

            if link_tag is not None:
                link = link_tag["href"]
                specific_news_links.append("https://www.bangkokpost.com" + link)

        return specific_news_links

    async def extract_content(self, url: str) -> Optional[NewsArticle]:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            downloaded = await fetch_article(session, url, headers)
            if downloaded is not None:
                try:
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
                        return article
                except Exception as e:
                    print(f"Error extracting content: {e}")
