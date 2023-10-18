from typing import Optional

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.interfaces.search_interface import IImageSearch
from channel_automation.models import ChannelInfo

from .base import BaseHandlers
from .utils import PhotoReplyFilter


class PostHandlers(BaseHandlers):
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

    async def process_article_and_send(
        self, context: ContextTypes.DEFAULT_TYPE, query, article_id: str
    ) -> None:
        news_article = self.es_repo.get_news_article_by_id(article_id)
        if news_article:
            await query.message.reply_text(
                "Processing the article, this may take up to a minute..."
            )
            processed_article = self.assistant.process_and_translate_article(
                news_article
            )
            print(processed_article.russian_abstract)
            images = self.search.search_images(processed_article.images_search, 25)
            processed_article.images_url = images
            self.es_repo.update_news_article(processed_article)

            await query.message.reply_text(
                f"Processing complete! Here's the generated post for article: *{processed_article.title}*",
                parse_mode="Markdown",
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

        # Retrieve the ChannelInfo by channel_id
        channel_info: Optional[ChannelInfo] = self.repo.get_channel_by_id(channel_id)

        # Retrieve the image URL and caption from the message
        message = query.message
        if message.photo:
            image_url = message.photo[-1].file_id
        else:
            image_url = None
        caption = message.caption_markdown

        # Add bottom_text from ChannelInfo to the caption if it exists
        if channel_info and channel_info.bottom_text:
            caption = f"{caption}\n\n{channel_info.bottom_text}"

        # Publish the article in the specified channel
        if image_url:
            await self.bot.send_photo(
                chat_id=channel_id,
                photo=image_url,
                caption=caption,
                parse_mode="Markdown",
            )
        else:
            await self.bot.send_message(
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
            else:
                await message.reply_text("Something went wrong. Regenerate the post.")


def register(app, bot, repo, es_repo, assistant, search, admin_chat_ids):
    logic = PostHandlers(bot, repo, es_repo, assistant, search, admin_chat_ids)
    app.add_handler(
        CallbackQueryHandler(logic.generate_post_callback, pattern="^generate_post:")
    )
    app.add_handler(
        CallbackQueryHandler(logic.regenerate_callback, pattern="^regenerate:")
    )
    app.add_handler(CallbackQueryHandler(logic.publish_callback, pattern="^publish:"))
    app.add_handler(
        CallbackQueryHandler(
            logic.publish_to_channel_callback, pattern="^publish_to_channel:"
        )
    )
    app.add_handler(CallbackQueryHandler(logic.back_callback, pattern="^back:"))
    app.add_handler(
        CallbackQueryHandler(logic.next_image_handler, pattern="^next_image:")
    )
    app.add_handler(MessageHandler(PhotoReplyFilter(), logic.handle_photo_reply))
