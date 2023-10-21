from telegram import Bot, ReplyKeyboardMarkup, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from channel_automation import assistant
from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.interfaces.search_interface import IImageSearch
from channel_automation.models import Admin
from channel_automation.services.bot import AWAITING_SECRET_KEY

from .base import BaseHandlers


def create_start_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["Active Sources"], ["Latest News"], ["Channels"]], resize_keyboard=True
    )  # `resize_keyboard=True` makes the keyboard fit the button sizes.


class AdminHandlers(BaseHandlers):
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

    async def is_user_admin(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        user_id = update.effective_user.id
        is_admin = str(user_id) in self.admin_chat_ids
        context.user_data["is_admin"] = is_admin
        return is_admin

    async def send_welcome_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        keyboard = create_start_menu()
        welcome_text = r"""*Welcome to the bot!*

    Here are some features you can use:
    1. **Reply with Photo**: If you reply to a social post with a photo, the photo will be attached to the post.
    2. **Reply with Text Guidance**: If you reply to a social post with text, your guidance will be applied to the post. For example, you can reply with commands like \`make it funnier\` or \`make it shorter\`.

    Feel free to explore!"""
        await update.message.reply_text(
            welcome_text, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = str(update.effective_user.id)
        if user_id not in self.admin_chat_ids:
            await update.message.reply_text(
                "Please enter the secret key to access this bot."
            )
            return AWAITING_SECRET_KEY

        await self.send_welcome_message(update, context)
        return ConversationHandler.END

    async def handle_secret_key(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        if update.message.text == self.secret_key:
            user_id = str(update.effective_user.id)
            username = (
                update.effective_user.username or update.effective_user.first_name
            )
            # Add this user_id to the database as admin
            self.repo.add_admin(Admin(user_id=user_id, name=username, is_active=True))
            # Update the local list of admin chat ids
            self.admin_chat_ids.append(user_id)
            await update.message.reply_text("You are now an admin!")
            await self.send_welcome_message(update, context)
            return ConversationHandler.END
        else:
            await update.message.reply_text("Incorrect key!")
            return AWAITING_SECRET_KEY

    async def get_user_id(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        await update.message.reply_text(f"Your user ID is: {user_id}")


def register(app, bot, repo, es_repo, assistant, search, admin_chat_ids):
    logic = AdminHandlers(bot, repo, es_repo, assistant, search, admin_chat_ids)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", logic.start)],
        states={
            AWAITING_SECRET_KEY: [
                MessageHandler(filters.TEXT, logic.handle_secret_key)
            ],
        },
        fallbacks=[],
    )
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("myid", logic.get_user_id))
