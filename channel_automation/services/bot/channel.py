from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    ChatMemberHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.interfaces.search_interface import IImageSearch
from channel_automation.models import ChannelInfo
from channel_automation.services.bot import EDITING_BUTTON_TEXT

from .base import BaseHandlers
from .utils import admin_required


class ChannelHandlers(BaseHandlers):
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

    @admin_required
    async def show_channels(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        channels = self.repo.get_all_channels()

        if not channels:
            await update.message.reply_text("No channels available.")
            return
        for channel in channels:
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Edit botton text", callback_data=f"edit_text:{channel.id}"
                        )
                    ]
                ]
            )

            bottom_text = channel.bottom_text or "No text"

            message_text = f"{channel.title} (ID: {channel.id})\n\n" f"{bottom_text}"

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_text,
                reply_markup=keyboard,
            )

    # Callback for edit button click
    async def edit_botton_text(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        query = update.callback_query
        _, channel_id = query.data.split(":", 1)

        await query.answer()
        await query.message.reply_text("Enter new botton text:")

        # Save channel id to retrieve later
        context.user_data["channel_id"] = channel_id

        return EDITING_BUTTON_TEXT

    async def save_channel_botton_text(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        new_text = update.message.text
        channel_id = context.user_data["channel_id"]

        channel = ChannelInfo(id=channel_id, bottom_text=new_text)
        self.repo.update_channel(channel)

        await update.message.reply_text("Botton text updated!")

        return ConversationHandler.END

    # Define a function to handle the ChatMemberUpdated event
    async def on_my_chat_member(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        my_chat_member = update.my_chat_member
        new_chat_member = my_chat_member.new_chat_member

        if (
            new_chat_member.user.id == context.bot.id
            and new_chat_member.status == "administrator"
        ):
            # Save the channel to the database
            channel = ChannelInfo(
                id=str(my_chat_member.chat.id), title=my_chat_member.chat.title
            )
            self.repo.add_channel(channel)

            # Send a message to all admins
            message_text = f"I've been added as an admin in the channel: {update.my_chat_member.chat.title}!"
            await self.send_message_to_all_admins(message_text)


def register(app, bot, repo, es_repo, assistant, search, admin_chat_ids):
    logic = ChannelHandlers(bot, repo, es_repo, assistant, search, admin_chat_ids)
    edit_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(logic.edit_botton_text, pattern="^edit_text:")
        ],
        states={
            EDITING_BUTTON_TEXT: [
                MessageHandler(filters.TEXT, logic.save_channel_botton_text)
            ],
        },
        fallbacks=[],
        per_message=False,
    )
    app.add_handler(edit_conv_handler)
    app.add_handler(MessageHandler(filters.Regex(r"^Channels$"), logic.show_channels))
    app.add_handler(ChatMemberHandler(logic.on_my_chat_member))
