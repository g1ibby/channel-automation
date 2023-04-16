from typing import List

from abc import ABC, abstractmethod

from channel_automation.models import NewsArticle


class INewsCrawlerService(ABC):
    @abstractmethod
    def crawl_and_extract_news_articles(self, main_page: str) -> list[NewsArticle]:
        """
        Crawl and extract news articles starting from the main page.

        Returns:
            List[NewsArticle]: A list of extracted NewsArticle instances.
        """
        pass

    @abstractmethod
    def schedule_news_crawling(self, interval_minutes: int = 30) -> None:
        """
        Schedule the crawling process to run every specified interval in minutes.

        Args:
            interval_minutes (int, optional): The interval in minutes between each crawling process. Defaults to 30.
        """
        pass
