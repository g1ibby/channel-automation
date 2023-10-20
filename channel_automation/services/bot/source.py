from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.interfaces.search_interface import IImageSearch
from channel_automation.models import NewsArticle, Source

from .base import BaseHandlers
from .utils import admin_required


class SourceHandlers(BaseHandlers):
    def __init__(
        self,
        bot: Bot,
        repo: IRepository,
        es_repo: IESRepository,
        assistant: IAssistant,
        search: IImageSearch,
        admin_chat_ids: list,
    ) -> None:
        super().__init__(bot, repo, es_repo, assistant, search, admin_chat_ids)

    @staticmethod
    def format_news_article(article: NewsArticle) -> str:
        return f"*{article.title}*\n[Read article]({article.source})"

    async def send_formatted_article(
        self,
        chat_ids: list[str],
        article: NewsArticle,
        generate_post_button: bool = True,
    ) -> None:
        formatted_article = self.format_news_article(article)

        reply_markup = None
        if generate_post_button:
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Generate post", callback_data=f"generate_post:{article.id}"
                        )
                    ],
                ]
            )

        for admin_chat_id in chat_ids:
            await self.bot.send_message(
                chat_id=admin_chat_id,
                text=formatted_article,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

    @admin_required
    async def add_source(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        link = " ".join(context.args)
        source = Source(link=link, is_active=True)
        self.repo.add_source(source)
        await update.message.reply_text(f"Source added: {link}")

    @admin_required
    async def disable_source(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        link = " ".join(context.args)
        source = self.repo.disable_source(link)
        if source:
            await update.message.reply_text(f"Source disabled: {link}")
        else:
            await update.message.reply_text("No such source found.")

    @admin_required
    async def get_active_sources(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        active_sources = self.repo.get_active_sources()
        response = "\n".join([source.link for source in active_sources])
        await update.message.reply_text(response)

    @admin_required
    async def get_latest_news(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        latest_articles = self.es_repo.get_latest_news(10)
        if not latest_articles:
            await update.message.reply_text("No articles found.")
            return

        for article in latest_articles:
            await self.send_formatted_article(
                [update.effective_chat.id], article, generate_post_button=True
            )


def register(app, bot, repo, es_repo, assistant, search, admin_chat_ids):
    logic = SourceHandlers(bot, repo, es_repo, assistant, search, admin_chat_ids)
    app.add_handler(CommandHandler("addsource", logic.add_source))
    app.add_handler(CommandHandler("disablesource", logic.disable_source))
    app.add_handler(
        MessageHandler(filters.Regex(r"^Active Sources$"), logic.get_active_sources)
    )
    app.add_handler(
        MessageHandler(filters.Regex(r"^Latest News$"), logic.get_latest_news)
    )
