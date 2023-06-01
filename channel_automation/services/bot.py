from typing import List

from telegram import (
    Bot,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
)
from telegram.ext.filters import BaseFilter

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.interfaces.bot_service_interface import ITelegramBotService
from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.interfaces.search_interface import IImageSearch
from channel_automation.models import ChannelInfo, NewsArticle, Source


class PhotoReplyFilter(BaseFilter):
    def filter(self, message):
        return message.photo is not None and message.reply_to_message is not None


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
        app.add_handler(
            CallbackQueryHandler(self.next_image_handler, pattern="^next_image:")
        )
        # app.add_handler(MessageHandler(Filters.reply, self.handle_reply))
        app.add_handler(MessageHandler(PhotoReplyFilter(), self.handle_photo_reply))

        app.run_polling()

    @staticmethod
    def create_original_keyboard(
        article_id: str, search_terms: str
    ) -> InlineKeyboardMarkup:
        google_search_url = f"https://www.google.com/search?tbm=isch&q={search_terms}"
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Regenerate", callback_data=f"regenerate:{article_id}"
                    ),
                    InlineKeyboardButton(
                        "Search image",
                        url=google_search_url,
                    ),
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

    async def handle_photo_reply(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message = update.message
        if message.reply_to_message.from_user.id == context.bot.id:
            # Get the photo file
            photo_file = message.photo[-1]  # use the highest resolution photo
            file_id = photo_file.file_id

            # Retrieve stored article_id and images_search
            data = context.chat_data.get(message.reply_to_message.message_id)
            if data:
                article_id = data.get("article_id")
                images_search = data.get("images_search")

                # Create keyboard for new message
                keyboard = self.create_original_keyboard(article_id, images_search)

                # Send a new message with the new photo
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=file_id,
                    caption=message.reply_to_message.caption,
                    reply_markup=keyboard,
                )

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

    async def process_article_and_send(
        self, context: ContextTypes.DEFAULT_TYPE, query, article_id: str
    ) -> None:
        news_article = self.es_repo.get_news_article_by_id(article_id)
        if news_article:
            processing_message = await query.message.reply_text(
                "Processing the article, this may take up to a minute..."
            )
            processed_article = self.assistant.process_and_translate_article(
                news_article
            )
            images = self.search.search_images(processed_article.images_search, 25)
            processed_article.images_url = images
            self.es_repo.update_news_article(processed_article)

            await processing_message.edit_text(
                "Processing complete! Here's the generated post:"
            )
            keyboard = self.create_original_keyboard(
                article_id, processed_article.images_search
            )

            sent_message = None
            # Send the post with the first image from Google search
            if processed_article.images_url:
                first_image_url = processed_article.images_url[0]
                sent_message = await query.message.reply_photo(
                    photo=first_image_url,
                    caption=f"{processed_article.russian_abstract}",
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            # If no images found, send the post without an image
            else:
                sent_message = await query.message.reply_text(
                    f"{processed_article.russian_abstract}",
                    parse_mode="Markdown",
                    reply_markup=keyboard,
                )
            # Store the article_id and images_search term with the sent message's id
            context.chat_data[sent_message.message_id] = {
                "article_id": article_id,
                "images_search": processed_article.images_search,
            }
        else:
            await query.message.reply_text("Article not found.")

    async def regenerate_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id = query.data.split(":", 1)

        await self.process_article_and_send(context, query, article_id)

        await query.answer(text=f"Regenerating post for article ID: {article_id}")

    async def generate_post_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id = query.data.split(":", 1)

        await self.process_article_and_send(context, query, article_id)

        await query.answer(text=f"Generating post for article ID: {article_id}")

    async def publish_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id = query.data.split(":", 1)
        # content_markdown
        # effective_attachment

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

        # Retrieve the image URL and caption from the message
        message = query.message
        if message.photo:
            image_url = message.photo[-1].file_id
        else:
            image_url = None
        caption = message.caption_markdown

        # Publish the article in the specified channel
        bot = Bot(token=self.token)
        if image_url:
            await bot.send_photo(
                chat_id=channel_id,
                photo=image_url,
                caption=caption,
                parse_mode="Markdown",
            )
        else:
            await bot.send_message(
                chat_id=channel_id,
                text=caption,
                parse_mode="Markdown",
            )

        # Update the inline keyboard markup using the new create_original_keyboard function
        keyboard = self.create_original_keyboard(article_id, "")

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
        keyboard = self.create_original_keyboard(article_id, "")

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

    async def next_image_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id, current_image_index = query.data.split(":", 2)

        news_article = self.es_repo.get_news_article_by_id(article_id)
        if news_article and news_article.images_url:
            new_image_index = (int(current_image_index) + 1) % len(
                news_article.images_url
            )
            new_image_url = news_article.images_url[new_image_index]

            keyboard = self.create_original_keyboard(article_id, "")

            # Send a new message with the updated image and caption
            await query.message.reply_photo(
                photo=new_image_url,
                caption=f"{news_article.russian_abstract}",
                parse_mode="Markdown",
                reply_markup=keyboard,
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
