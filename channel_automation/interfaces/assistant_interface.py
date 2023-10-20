from typing import Optional

from abc import ABC, abstractmethod

from channel_automation.models import NewsArticle, Post


class IAssistant(ABC):
    @abstractmethod
    def generate_post(self, news_article: NewsArticle, variation_number: int) -> Post:
        """
        Generate abstract and translate the specified fields of a NewsArticle instance, then return the social post.

        Args:
            news_article (NewsArticle): The NewsArticle instance to be processed and translated.

        Returns:
            Post: The generated social post.
        """
        pass
