from typing import Callable, List, Optional

import json

import aiohttp
import trafilatura
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_random_exponential

from channel_automation.models import (
    NewsArticle,  # Make sure this import path is correct
)

from ..utils import news_article_from_json  # Make sure this import path is correct

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


def extract_main_image(html_content: bytes) -> Optional[str]:
    # Parse the HTML content
    soup = BeautifulSoup(html_content, "lxml")
    # Find the img tag within the class "c-article-image-video"
    img_tag = soup.select_one(
        ".c-article-image-video .js-poster-img.c-article-media__img"
    )

    # If img tag exists and has 'src' attribute, return the URL
    if img_tag and "src" in img_tag.attrs:
        return img_tag["src"]
    return None


class EuronewsTourismCrawler:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.filters: list[Callable[[str], bool]] = [
            lambda url: "/live-news/" not in url  # you can add more filters here
        ]

    async def crawl(self) -> list[NewsArticle]:
        print("Crawling Euronews Tourism")
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
            news_links = self.extract_news_links(html_content)
            for url in news_links:
                if all(filter_func(url) for filter_func in self.filters):
                    filtered_news_links.append(url)
        return filtered_news_links

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        if not html_content:
            return []

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(html_content, "lxml")

        # Initialize an empty list to store the scraped article URLs
        article_links = []

        # Find all 'article' elements within the div class "o-block-listing__articles"
        articles = soup.find("div", {"class": "o-block-listing__articles"}).find_all(
            "article"
        )

        # Loop through each 'article' element and extract the article URL
        for article in articles:
            a_tag = article.find("a", {"class": "media__img__link"})
            if a_tag:
                article_url = a_tag.get("href")

                # Add the prefix to each article URL
                full_url = f"https://www.euronews.com{article_url}"

                article_links.append(full_url)

        return article_links

    async def extract_content(self, url: str) -> Optional[NewsArticle]:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            downloaded = await fetch_url(session, url, headers)
            if downloaded:
                # You can replace this line with your actual image extraction function
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
