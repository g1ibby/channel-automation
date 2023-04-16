from typing import List

from abc import ABC, abstractmethod

from channel_automation.models import NewsArticle


class INewsArticleRepository(ABC):
    @abstractmethod
    def save_news_article(self, news_article: NewsArticle) -> NewsArticle:
        """
        Save a news article to Elasticsearch.

        Args:
            news_article (NewsArticle): A NewsArticle instance to be saved.

        Returns:
            NewsArticle: The saved NewsArticle instance.
        """
        pass

    @abstractmethod
    def get_latest_news(self, count: int) -> list[NewsArticle]:
        """
        Retrieve the latest news articles from Elasticsearch.

        Args:
            count (int): The number of latest news articles to retrieve.

        Returns:
            List[NewsArticle]: A list of the latest NewsArticle instances.
        """
        pass
