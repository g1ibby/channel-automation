from typing import Optional

from abc import ABC, abstractmethod

from channel_automation.models import NewsArticle


class IAssistant(ABC):
    @abstractmethod
    def process_and_translate_article(
        self, news_article: NewsArticle, variation_number: int
    ) -> NewsArticle:
        """
        Generate abstract and translate the specified fields of a NewsArticle instance, then return the modified instance.

        Args:
            news_article (NewsArticle): The NewsArticle instance to be processed and translated.

        Returns:
            NewsArticle: The processed and translated NewsArticle instance.
        """
        pass
