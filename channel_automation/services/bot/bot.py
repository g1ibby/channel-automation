import html
import json
import logging
import traceback

from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes
from telegram.request import HTTPXRequest

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.interfaces.bot_service_interface import ITelegramBotService
from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.interfaces.search_interface import IImageSearch
from channel_automation.models import NewsArticle

from . import admin, channel, post, source

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

DEVELOPER_CHAT_ID = 1672563160


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
        request = HTTPXRequest(
            connection_pool_size=20, connect_timeout=20.0, http_version="2.0"
        )
        self.bot = Bot(token=self.token, request=request)

    def run(self) -> None:
        app = ApplicationBuilder().token(self.token).build()
        app.add_error_handler(self.error_handler)

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

    async def error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        logger.error("Exception while handling an update:", exc_info=context.error)

        tb_list = traceback.format_exception(
            None, context.error, context.error.__traceback__
        )
        tb_string = "".join(tb_list)

        update_str = update.to_dict() if update else str(update)
        message = (
            "An exception was raised while handling an update\n"
            f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
            "</pre>\n\n"
            f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
            f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
            f"<pre>{html.escape(tb_string)}</pre>"
        )
        await self.bot.send_message(
            chat_id=DEVELOPER_CHAT_ID,
            text=message,
            parse_mode=ParseMode.HTML,
        )
