from typing import Callable, Optional

import asyncio
import json
from abc import ABC, abstractmethod

import aiohttp
import trafilatura
from tenacity import retry, stop_after_attempt, wait_random_exponential

from channel_automation.models import NewsArticle

from ..utils import news_article_from_json


class BaseWebCrawler(ABC):
    """
    Abstract base class for a web crawler that fetches and extracts news articles.
    """

    DEFAULT_TIMEOUT_SECONDS = 15  # Default timeout for HTTP requests

    def __init__(
        self,
        base_url: str,
        headers: Optional[dict[str, str]] = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """
        Initializes the web crawler with a base URL, optional headers, and a timeout.
        """
        self.base_url = base_url
        self.headers = headers if headers is not None else {}
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.filters: list[Callable[[str], bool]] = []
        self.session = None  # Session will be created when needed

    async def __aenter__(self):
        """
        Asynchronous context manager entry point that ensures a session is created.
        """
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """
        Asynchronous context manager exit point that closes the session.
        """
        await self.session.close()

    async def crawl(self) -> list[str]:
        """
        Crawls for news articles and returns a list of URLs on news articles.
        """
        class_name = self.__class__.__name__
        print(f"Crawling {class_name}")
        news_links = await self.crawl_news_links()
        unique_news_links = list(
            set(news_links)
        )  # Remove duplicates by converting to a set and back to a list
        print(f"Found {len(unique_news_links)} unique news articles using {class_name}")
        return unique_news_links

    async def crawl_news_links(self) -> list[str]:
        """
        Fetches the base URL and extracts a list of news links applying filters.
        """
        html_content = await self.fetch(self.base_url)
        news_links = self.extract_news_links(html_content)
        return [
            url
            for url in news_links
            if all(filter_func(url) for filter_func in self.filters)
        ]

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random_exponential(multiplier=1, min=3, max=30),
    )
    async def fetch(self, url: str) -> Optional[str]:
        """
        Fetches content from a URL as text and returns it, or None if an error occurred.
        """
        if self.session is None:  # Check if the session exists
            raise RuntimeError(
                "Session has not been created. Use 'async with' block or call '__aenter__' manually."
            )
        try:
            async with self.session.get(url, headers=self.headers) as response:
                response.raise_for_status()
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Received status code {response.status}")
                    return None
        except aiohttp.ClientError as e:
            print(f"Error fetching {url}: {e}")
            return None

    async def extract_articles(
        self, news_links: list[str], parallel: bool = True
    ) -> list[NewsArticle]:
        """
        Given a list of news links, extracts content from each link and returns a list of NewsArticle objects.
        Can run in parallel or sequential mode based on the 'parallel' flag.
        """
        if parallel:
            tasks = [self.extract_content(link) for link in news_links]
            articles = await asyncio.gather(*tasks)
        else:
            articles = []
            for link in news_links:
                article = await self.extract_content(link)
                articles.append(article)

        # Filter out None values in case some articles failed to be fetched or extracted
        return [article for article in articles if article]

    async def extract_content(self, url: str) -> Optional[NewsArticle]:
        """
        Extracts content from a given URL and returns a NewsArticle object or None.
        """
        downloaded = await self.fetch(url)
        if downloaded:
            return await self.create_article_from_content(downloaded)

    async def create_article_from_content(self, content: str) -> Optional[NewsArticle]:
        """
        Creates a NewsArticle object from the downloaded content string.
        """
        main_image_url = self.extract_main_image(content)
        extracted_data = trafilatura.extract(
            content,
            include_comments=False,
            with_metadata=True,
            favor_precision=True,
            deduplicate=True,
            output_format="json",
        )
        if extracted_data:
            data = json.loads(extracted_data)
            article = await news_article_from_json(data)
            article.images_url = article.images_url or []
            if main_image_url:
                article.images_url.append(main_image_url)
            return article
        return None

    @abstractmethod
    def extract_main_image(self, html_content: Optional[str]) -> Optional[str]:
        """
        Abstract method to extract the main image URL from HTML content.
        """
        pass

    @abstractmethod
    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        """
        Abstract method to extract news links from HTML content.
        """
        pass
