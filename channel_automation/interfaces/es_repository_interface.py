from typing import List, Optional

from abc import ABC, abstractmethod

from channel_automation.models import NewsArticle


class IESRepository(ABC):
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

    @abstractmethod
    def update_news_article(self, news_article: NewsArticle) -> NewsArticle:
        """
        Update an existing news article in Elasticsearch.

        Args:
            news_article (NewsArticle): A NewsArticle instance with updated data.

        Returns:
            NewsArticle: The updated NewsArticle instance.
        """
        pass

    @abstractmethod
    def get_news_article_by_id(self, article_id: str) -> Optional[NewsArticle]:
        """
        Retrieve a news article from Elasticsearch by its ID.

        Args:
            article_id (str): The ID of the news article to retrieve.

        Returns:
            Optional[NewsArticle]: The retrieved NewsArticle instance, or None if not found.
        """
        pass
