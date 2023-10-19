import asyncio
import re

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.interfaces.search_interface import IImageSearch
from channel_automation.models import ChannelInfo

from .base import BaseHandlers
from .utils import PhotoReplyFilter

ATTEMPTS_GENERATE = 3


async def send_error_message(retry_state):
    query = retry_state.args[2]
    if retry_state.attempt_number < ATTEMPTS_GENERATE:
        await query.message.reply_text(
            f"Something went wrong with generating post text. I will try again. Attempt {retry_state.attempt_number}"
        )
    else:
        await query.message.reply_text(
            f"Sorry, I give up. GPT returned a wrong answer {ATTEMPTS_GENERATE} times."
        )


def before_sleep_callback(retry_state):
    asyncio.run_coroutine_threadsafe(
        send_error_message(retry_state), asyncio.get_event_loop()
    )


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

    @staticmethod
    def create_variations_keyboard(article_id: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Variation One", callback_data=f"variation_one:{article_id}"
                    ),
                    InlineKeyboardButton(
                        "Variation Two", callback_data=f"variation_two:{article_id}"
                    ),
                ],
                [InlineKeyboardButton("Back", callback_data=f"back:{article_id}")],
            ]
        )

    @retry(
        stop=stop_after_attempt(ATTEMPTS_GENERATE),  # Stop after 5 attempts
        wait=wait_fixed(3),  # Wait 5 seconds between attempts
        retry=retry_if_exception_type(Exception),  # Retry if there's an exception
        before_sleep=before_sleep_callback,  # Custom message function
    )
    async def process_article_and_send(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        query,
        article_id: str,
        variation_number: int,
    ) -> None:
        news_article = self.es_repo.get_news_article_by_id(article_id)
        if news_article:
            await query.message.reply_text(
                "Processing the article, this may take up to a few minutes..."
            )
            try:
                processed_article = self.assistant.process_and_translate_article(
                    news_article,
                    variation_number,
                )
            except Exception as e:
                print(e)
                raise e

            try:
                images = self.search.search_images(processed_article.images_search, 25)
                processed_article.images_url = images
            except Exception as e:
                print(e)
                await query.message.reply_text(
                    "Something went wrong with searching images. You can add image manually later."
                )

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

    async def variation_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, variation_number: int
    ) -> None:
        query = update.callback_query
        _, article_id = query.data.split(":", 1)

        await self.process_article_and_send(
            context, query, article_id, variation_number
        )
        await query.answer(
            text=f"Generated variation {variation_number} for article ID: {article_id}"
        )

    async def regenerate_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id = query.data.split(":", 1)

        new_keyboard = self.create_variations_keyboard(article_id)
        await query.edit_message_reply_markup(reply_markup=new_keyboard)

    async def generate_post_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id = query.data.split(":", 1)

        new_keyboard = self.create_variations_keyboard(article_id)
        await query.edit_message_reply_markup(reply_markup=new_keyboard)

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
    app.add_handler(
        CallbackQueryHandler(
            lambda update, context: logic.variation_callback(update, context, 1),
            pattern="^variation_one:",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            lambda update, context: logic.variation_callback(update, context, 2),
            pattern="^variation_two:",
        )
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
