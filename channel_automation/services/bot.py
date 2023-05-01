from typing import List

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
)

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.interfaces.bot_service_interface import ITelegramBotService
from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.interfaces.search_interface import IImageSearch
from channel_automation.models import ChannelInfo, NewsArticle, Source


class TelegramBotService(ITelegramBotService):
    def __init__(
        self,
        token: str,
        admin_chat_id: str,
        repository: IRepository,
        es_repo: IESRepository,
        assistant: IAssistant,
        search: IImageSearch,
    ):
        self.token = token
        self.admin_chat_id = admin_chat_id
        self.repo = repository
        self.es_repo = es_repo
        self.assistant = assistant
        self.search = search

    def run(self) -> None:
        app = ApplicationBuilder().token(self.token).build()
        app.add_handler(ChatMemberHandler(self.on_my_chat_member))
        app.add_handler(CommandHandler("addsource", self.add_source))
        app.add_handler(CommandHandler("disablesource", self.disable_source))
        app.add_handler(CommandHandler("activesources", self.get_active_sources))
        app.add_handler(CommandHandler("myid", self.get_user_id))
        app.add_handler(CommandHandler("latestnews", self.get_latest_news))
        app.add_handler(CommandHandler("channels", self.show_channels))
        app.add_handler(
            CallbackQueryHandler(self.generate_post_callback, pattern="^generate_post:")
        )
        app.add_handler(
            CallbackQueryHandler(self.regenerate_callback, pattern="^regenerate:")
        )
        app.add_handler(
            CallbackQueryHandler(self.publish_callback, pattern="^publish:")
        )
        app.add_handler(
            CallbackQueryHandler(
                self.publish_to_channel_callback, pattern="^publish_to_channel:"
            )
        )
        app.add_handler(CallbackQueryHandler(self.back_callback, pattern="^back:"))

        app.run_polling()

    @staticmethod
    def create_original_keyboard(article_id: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Regenerate", callback_data=f"regenerate:{article_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "Publish", callback_data=f"publish:{article_id}"
                    )
                ],
            ]
        )

    @staticmethod
    def create_channel_keyboard(
        article_id: str, channels: list[ChannelInfo]
    ) -> InlineKeyboardMarkup:
        channel_buttons = [
            InlineKeyboardButton(
                channel.title,
                callback_data=f"publish_to_channel:{article_id}:{channel.id}",
            )
            for channel in channels
        ]
        back_button = InlineKeyboardButton("Back", callback_data=f"back:{article_id}")
        return InlineKeyboardMarkup([channel_buttons, [back_button]])

    @staticmethod
    def format_latest_news_article(article: NewsArticle) -> str:
        return f"*{article.title}*\n[Read article]({article.source})"

    async def show_channels(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        channels = self.repo.get_all_channels()

        if not channels:
            response = "No channels available."
        else:
            response = "Available channels:\n"
            for channel in channels:
                response += f"{channel.title} (ID: {channel.id})\n"

        await update.message.reply_text(response)

    # Define a function to handle the ChatMemberUpdated event
    async def on_my_chat_member(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        bot = Bot(token=self.token)
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

            await bot.send_message(
                chat_id=self.admin_chat_id,
                text=f"I've been added as an admin in the channel: {update.my_chat_member.chat.title}!",
            )

    async def process_article_and_send(self, query, article_id: str) -> None:
        news_article = self.es_repo.get_news_article_by_id(article_id)
        if news_article:
            processing_message = await query.message.reply_text(
                "Processing the article, this may take up to a minute..."
            )
            processed_article = self.assistant.process_and_translate_article(
                news_article
            )
            self.es_repo.update_news_article(processed_article)

            images = self.search.search_images(processed_article.images_search, 5)

            await processing_message.edit_text(
                "Processing complete! Here's the generated post:"
            )

            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Regenerate", callback_data=f"regenerate:{article_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "Publish", callback_data=f"publish:{article_id}"
                        )
                    ],
                ]
            )

            # Send the post with the first image from Google search
            if images:
                first_image_url = images[0]
                await query.message.reply_photo(
                    photo=first_image_url,
                    caption=f"{processed_article.russian_abstract}",
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            # If no images found, send the post without an image
            else:
                await query.message.reply_text(
                    f"{processed_article.russian_abstract}",
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            await query.message.reply_text(
                processed_article.images_search
            )  # TODO: remove this line
        else:
            await query.message.reply_text("Article not found.")

    async def regenerate_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id = query.data.split(":", 1)

        await self.process_article_and_send(query, article_id)

        await query.answer(text=f"Regenerating post for article ID: {article_id}")

    async def generate_post_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id = query.data.split(":", 1)

        await self.process_article_and_send(query, article_id)

        await query.answer(text=f"Generating post for article ID: {article_id}")

    async def publish_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id = query.data.split(":", 1)

        # Get all available channels from the database
        channels = self.repo.get_all_channels()

        # Update the inline keyboard markup using the new create_channel_keyboard function
        keyboard = self.create_channel_keyboard(article_id, channels)

        await query.edit_message_reply_markup(reply_markup=keyboard)

    async def publish_to_channel_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id, channel_id = query.data.split(":", 2)

        # Retrieve the article by ID
        article = self.es_repo.get_news_article_by_id(article_id)

        # Publish the article in the specified channel
        bot = Bot(token=self.token)
        await bot.send_message(
            chat_id=channel_id,
            text=f"{article.russian_abstract}",
            parse_mode="Markdown",
        )

        # Update the inline keyboard markup using the new create_original_keyboard function
        keyboard = self.create_original_keyboard(article_id)

        # Update the inline keyboard markup of the message
        await query.edit_message_reply_markup(reply_markup=keyboard)

        await query.answer(
            text=f"Published post for article ID: {article_id} in channel ID: {channel_id}"
        )

    async def back_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id = query.data.split(":", 1)

        # Update the inline keyboard markup using the new create_original_keyboard function
        keyboard = self.create_original_keyboard(article_id)

        await query.edit_message_reply_markup(reply_markup=keyboard)

    async def get_latest_news(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        latest_articles = self.es_repo.get_latest_news(5)

        for article in latest_articles:
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Generate post", callback_data=f"generate_post:{article.id}"
                        )
                    ],
                ]
            )

            await update.message.reply_text(
                self.format_latest_news_article(article),
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

    async def get_user_id(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_id = update.effective_user.id
        await update.message.reply_text(f"Your user ID is: {user_id}")

    async def send_article_to_admin(self, article: NewsArticle) -> None:
        bot = Bot(token=self.token)
        await bot.send_message(
            chat_id=self.admin_chat_id,
            text=f"*{article.title}*\n{article.source}",
        )

    async def add_source(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        link = " ".join(context.args)
        source = Source(link=link, is_active=True)
        self.repo.add_source(source)
        await update.message.reply_text(f"Source added: {link}")

    async def disable_source(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        link = " ".join(context.args)
        source = self.repo.disable_source(link)
        if source:
            await update.message.reply_text(f"Source disabled: {link}")
        else:
            await update.message.reply_text("No such source found.")

    async def get_active_sources(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        active_sources = self.repo.get_active_sources()
        response = "\n".join([source.link for source in active_sources])
        await update.message.reply_text(response)
