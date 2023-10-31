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
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "DNT": "1",
    "Connection": "keep-alive",
    "Cookie": "PHPSESSID=e9ced6913e0a79c782afcf59d242aafe",
    "Upgrade-Insecure-Requests": "1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, min=3, max=30),
)
async def fetch_url(session, url, headers):
    async with session.get(url, headers=headers) as response:
        response.raise_for_status()  # Raise an exception for HTTP errors
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
        response.raise_for_status()  # Raise an exception for HTTP errors
        if response.status == 200:
            return await response.read()
        else:
            print(f"Received status code {response.status}")
            return None


def extract_main_image(html_content: bytes) -> Optional[str]:
    soup = BeautifulSoup(html_content, "html.parser")
    img_tag = soup.find("img", {"class": "img-fluid"})
    if img_tag and "src" in img_tag.attrs:
        return img_tag["src"]
    return None


class PhuketNewsCrawler:
    def __init__(self) -> None:
        self.filters: list[Callable[[str], bool]] = [
            lambda url: "/live-news/" not in url
        ]

    async def crawl(self) -> list[NewsArticle]:
        print("Crawling Phuket News")
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
            url = "https://www.thephuketnews.com/sport-thailand.php"
            html_content = await fetch_url(session, url, headers)
            news_links = self.extract_news_links(html_content)
            for url in news_links:
                if all(filter_func(url) for filter_func in self.filters):
                    filtered_news_links.append(url)
        return filtered_news_links

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        if not html_content:
            return []
        soup = BeautifulSoup(html_content, "html.parser")
        links = []
        for item in soup.select(".row.p-2.border-bottom"):
            link = item.select_one("h5 a")["href"]
            full_link = f"https://www.thephuketnews.com{link}"
            links.append(full_link)
        return links

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
