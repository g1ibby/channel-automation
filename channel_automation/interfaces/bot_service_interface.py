from abc import ABC, abstractmethod

from channel_automation.models import NewsArticle


class ITelegramBotService(ABC):
    @abstractmethod
    def run(self) -> None:
        """
        Run the Telegram bot.
        """
        pass

    @abstractmethod
    async def send_article_to_admin(self, article: NewsArticle) -> None:
        """
        Send a NewsArticle to the admin.

        Args:
            article (NewsArticle): The news article to send.
        """
        pass
