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

    @abstractmethod
    def make_post_fancy(self, post: Post) -> Post:
        """
        Make the specified post fancy.

        Args:
            post (Post): The post to be made fancy.

        Returns:
            Post: The fancy post.
        """
        pass

    @abstractmethod
    def post_guidence(self, post: Post, guidence: str) -> Post:
        """
        Add guidence to the specified post.

        Args:
            post (Post): The post to be added guidence.
            guidence (str): The guidence to be added.

        Returns:
            Post: The post with guidence.
        """
