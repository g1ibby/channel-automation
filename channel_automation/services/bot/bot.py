from telegram import Bot
from telegram.ext import ApplicationBuilder

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.interfaces.bot_service_interface import ITelegramBotService
from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.interfaces.search_interface import IImageSearch
from channel_automation.models import NewsArticle

from . import admin, channel, post, source


class TelegramBotService(ITelegramBotService):
    def __init__(
        self,
        token: str,
        repo: IRepository,
        es_repo: IESRepository,
        assistant: IAssistant,
        search: IImageSearch,
    ):
        self.token = token
        self.repo = repo
        self.es_repo = es_repo
        self.assistant = assistant
        self.search = search
        self.admin_chat_ids = [admin.user_id for admin in self.repo.get_active_admins()]
        self.bot = Bot(token=self.token)

    def run(self) -> None:
        app = ApplicationBuilder().token(self.token).build()

        admin.register(
            app,
            self.bot,
            self.repo,
            self.es_repo,
            self.assistant,
            self.search,
            self.admin_chat_ids,
        )
        channel.register(
            app,
            self.bot,
            self.repo,
            self.es_repo,
            self.assistant,
            self.search,
            self.admin_chat_ids,
        )
        source.register(
            app,
            self.bot,
            self.repo,
            self.es_repo,
            self.assistant,
            self.search,
            self.admin_chat_ids,
        )
        post.register(
            app,
            self.bot,
            self.repo,
            self.es_repo,
            self.assistant,
            self.search,
            self.admin_chat_ids,
        )

        app.run_polling()

    async def send_article_to_admin(self, article: NewsArticle) -> None:
        handlers = source.SourceHandlers(
            self.bot,
            self.repo,
            self.es_repo,
            self.assistant,
            self.search,
            self.admin_chat_ids,
        )
        await handlers.send_formatted_article(self.admin_chat_ids, article)
