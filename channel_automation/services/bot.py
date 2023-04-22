from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from channel_automation.interfaces.bot_service_interface import ITelegramBotService
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.models import NewsArticle, Source


class TelegramBotService(ITelegramBotService):
    def __init__(self, token: str, admin_chat_id: str, repository: IRepository):
        self.token = token
        self.admin_chat_id = admin_chat_id
        self.repository = repository

    def run(self) -> None:
        app = ApplicationBuilder().token(self.token).build()
        app.add_handler(CommandHandler("addsource", self.add_source))
        app.add_handler(CommandHandler("disablesource", self.disable_source))
        app.add_handler(CommandHandler("activesources", self.get_active_sources))
        app.add_handler(CommandHandler("myid", self.get_user_id))
        app.run_polling()

    async def get_user_id(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        await update.message.reply_text(f"Your user ID is: {user_id}")

    async def send_article_to_admin(self, article: NewsArticle) -> None:
        app = ApplicationBuilder().token(self.token).build()
        await app.send_message(
            chat_id=self.admin_chat_id,
            text=f"*{article.title}*\n{article.link}",
        )

    async def add_source(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        link = " ".join(context.args)
        source = Source(link=link, is_active=True)
        self.repository.add_source(source)
        await update.message.reply_text(f"Source added: {link}")

    async def disable_source(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        link = " ".join(context.args)
        source = self.repository.disable_source(link)
        if source:
            await update.message.reply_text(f"Source disabled: {link}")
        else:
            await update.message.reply_text("No such source found.")

    async def get_active_sources(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        active_sources = self.repository.get_active_sources()
        response = "\n".join([source.link for source in active_sources])
        await update.message.reply_text(response)
