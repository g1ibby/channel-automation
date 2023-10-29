from typing import Optional

import asyncio

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler, filters
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.interfaces.search_interface import IImageSearch
from channel_automation.models import ChannelInfo

from .base import BaseHandlers

ATTEMPTS_GENERATE = 3


async def send_error_message(retry_state):
    query = retry_state.args[2]  # query is the third argument
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


def create_channel_keyboard(
    article_id: str, post_index: int, channels: list[ChannelInfo]
) -> InlineKeyboardMarkup:
    channel_buttons = [
        InlineKeyboardButton(
            channel.title,
            callback_data=f"publish_to_channel:{article_id}:{post_index}:{channel.id}",
        )
        for channel in channels
    ]
    back_button = InlineKeyboardButton(
        "Back", callback_data=f"back:{article_id}:{post_index}"
    )
    return InlineKeyboardMarkup([channel_buttons, [back_button]])


def create_original_keyboard(
    article_id: str, post_index: int, search_terms: Optional[str]
) -> InlineKeyboardMarkup:
    google_search_url = f"https://www.google.com/search?tbm=isch&q={search_terms}"
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Regenerate", callback_data=f"regenerate:{article_id}:{post_index}"
                ),
                InlineKeyboardButton(
                    "Search image",
                    url=google_search_url,
                ),
            ],
            [
                InlineKeyboardButton(
                    "Make fancy", callback_data=f"make_fancy:{article_id}:{post_index}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "Publish", callback_data=f"publish:{article_id}:{post_index}"
                )
            ],
        ]
    )


def create_variations_keyboard(
    article_id: str, post_index: int, back=True
) -> InlineKeyboardMarkup:
    keyboard_layout = [
        [
            InlineKeyboardButton(
                "Variation One", callback_data=f"variation_one:{article_id}"
            ),
            InlineKeyboardButton(
                "Variation Two", callback_data=f"variation_two:{article_id}"
            ),
        ]
    ]
    if back:
        keyboard_layout.append(
            [
                InlineKeyboardButton(
                    "Back", callback_data=f"back:{article_id}:{post_index}"
                )
            ]
        )

    return InlineKeyboardMarkup(keyboard_layout)


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

    async def send_post(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        chat_id,
        article_id: str,
        post_index: int,
    ) -> Optional[str]:
        news_article = self.es_repo.get_news_article_by_id(article_id)
        if news_article:
            post = news_article.posts[post_index]
            if post:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=f"Here's the generated post for article: *{news_article.title}*",
                    parse_mode="Markdown",
                )
                keyboard = create_original_keyboard(
                    article_id, post_index, post.images_search
                )
                if post.images_id:
                    # Use the first image_id from images_id list
                    image_to_use = post.images_id[0]
                elif post.images_url:
                    # Use the first image_url from images_url list
                    image_to_use = post.images_url[0]
                else:
                    image_to_use = None

                image_id = None
                if image_to_use:
                    sent_message = await self.bot.send_photo(
                        chat_id=chat_id,
                        photo=image_to_use,
                        caption=f"{post.social_post}",
                        parse_mode="Markdown",
                        reply_markup=keyboard,
                    )
                    image_id = sent_message.photo[-1].file_id
                else:
                    sent_message = await self.bot.send_message(
                        chat_id=chat_id,
                        text=f"{post.social_post}",
                        parse_mode="Markdown",
                        reply_markup=keyboard,
                    )
                print(f"Message ID: {sent_message.message_id}")
                context.chat_data[sent_message.message_id] = {
                    "article_id": article_id,
                    "post_index": post_index,
                }
                return image_id
            else:
                await self.bot.send_message(chat_id=chat_id, text="Post not found.")
        else:
            await self.bot.send_message(chat_id=chat_id, text="Article not found.")

    @retry(
        stop=stop_after_attempt(ATTEMPTS_GENERATE),  # Stop after 5 attempts
        wait=wait_fixed(3),  # Wait 5 seconds between attempts
        retry=retry_if_exception_type(Exception),  # Retry if there's an exception
        before_sleep=before_sleep_callback,  # Custom message function
    )
    async def generate_post(
        self,
        context: ContextTypes.DEFAULT_TYPE,
        query,
        article_id: str,
        variation_number: int,
    ) -> None:
        print(article_id)
        news_article = self.es_repo.get_news_article_by_id(article_id)
        if not news_article:
            await query.message.reply_text("Article not found.")
            return

        await query.message.reply_text(
            "Processing the article, this may take up to a few minutes..."
        )
        try:
            post = self.assistant.generate_post(
                news_article,
                variation_number,
            )
            if post:
                news_article.posts.append(post)
                post_index = len(news_article.posts) - 1
        except Exception as e:
            print(e)
            raise e

        print(f"Generated post: {post.social_post}")

        try:
            images = []
            if (
                news_article.images_url is not None
                and len(news_article.images_url) != 0
            ):
                images = news_article.images_url
            else:
                images = self.search.search_images(post.images_search, 25)
            if images:
                first_image_url = images[0]
                news_article.posts[post_index].images_url.append(first_image_url)
        except Exception as e:
            print(e)
            await query.message.reply_text(
                "Something went wrong with searching images. You can add image manually later."
            )

        self.es_repo.update_news_article(news_article)
        chat_id = query.message.chat_id
        image_id = await self.send_post(context, chat_id, article_id, post_index)
        try:
            if image_id:
                news_article.posts[post_index].images_id = [
                    image_id
                ]  # rewrite images_id with the new image_id
                self.es_repo.update_news_article(news_article)
        except Exception as e:
            print(e)
            await query.message.reply_text(
                "Something went wrong with saving the image. You can add image manually later."
            )

    @retry(
        stop=stop_after_attempt(ATTEMPTS_GENERATE),  # Stop after 5 attempts
        wait=wait_fixed(3),  # Wait 5 seconds between attempts
        retry=retry_if_exception_type(Exception),  # Retry if there's an exception
        before_sleep=before_sleep_callback,  # Custom message function
    )
    async def fancy_post(self, context, query, article_id: str, post_index: int):
        news_article = self.es_repo.get_news_article_by_id(article_id)
        if not news_article:
            await query.message.reply_text("Article not found.")
            return

        await query.message.reply_text(
            "Making the post *fancy*...", parse_mode="Markdown"
        )
        post = news_article.posts[post_index]
        fancy_post = self.assistant.make_post_fancy(post)
        print(f"Fancy post: {fancy_post}")
        if fancy_post:
            news_article.posts.append(fancy_post)
            post_index = len(news_article.posts) - 1
            self.es_repo.update_news_article(news_article)
            await self.send_post(context, query.message.chat_id, article_id, post_index)

    @retry(
        stop=stop_after_attempt(ATTEMPTS_GENERATE),  # Stop after 5 attempts
        wait=wait_fixed(3),  # Wait 5 seconds between attempts
        retry=retry_if_exception_type(Exception),  # Retry if there's an exception
        before_sleep=before_sleep_callback,  # Custom message function
    )
    async def guidence_post(
        self, context, message, article_id: str, post_index: int, guidence: str
    ):
        news_article = self.es_repo.get_news_article_by_id(article_id)
        if not news_article:
            await message.reply_text("Article not found.")
            return

        await message.reply_text(
            "Applying your guidence to this post", parse_mode="Markdown"
        )
        post = news_article.posts[post_index]
        guided_post = self.assistant.post_guidence(post, guidence)
        print(f"Guided post: {guided_post}")
        if guided_post:
            news_article.posts.append(guided_post)
            post_index = len(news_article.posts) - 1
            self.es_repo.update_news_article(news_article)
            await self.send_post(context, message.chat.id, article_id, post_index)

    async def make_post_fancy_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id, post_index = query.data.split(":", 2)
        post_index = int(post_index)
        print(f"Making post fancy: {post_index} for article: {article_id}")

        await self.fancy_post(context, query, article_id, post_index)

    async def chosen_variation_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, variation_number: int
    ) -> None:
        query = update.callback_query
        _, article_id = query.data.split(":", 1)
        print(f"Chosen variation: {variation_number} for article: {article_id}")

        await self.generate_post(context, query, article_id, variation_number)

    async def regenerate_post_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id, post_index = query.data.split(":", 2)

        new_keyboard = create_variations_keyboard(article_id, post_index)
        await query.edit_message_reply_markup(reply_markup=new_keyboard)

    async def generate_post_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id = query.data.split(":", 1)

        new_keyboard = create_variations_keyboard(article_id, 0, False)
        await query.edit_message_reply_markup(reply_markup=new_keyboard)

    async def publish_menu_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id, post_index = query.data.split(":", 2)
        post_index = int(post_index)

        # Get all available channels from the database
        channels = self.repo.get_all_channels()
        # Update the inline keyboard markup using the new create_channel_keyboard function
        keyboard = create_channel_keyboard(article_id, post_index, channels)

        await query.edit_message_reply_markup(reply_markup=keyboard)

    async def publish_to_channel_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id, post_index, channel_id = query.data.split(":", 3)
        post_index = int(post_index)
        print(f"Publishing post {post_index} for article {article_id}")

        try:
            article = self.es_repo.get_news_article_by_id(article_id)
            post = article.posts[post_index]

            # Retrieve the ChannelInfo by channel_id
            channel_info: Optional[ChannelInfo] = self.repo.get_channel_by_id(
                channel_id
            )

            # Retrieve the image URL and caption from the message
            caption = post.social_post
            # Add bottom_text from ChannelInfo to the caption if it exists
            if channel_info and channel_info.bottom_text:
                caption = f"{caption}\n\n{channel_info.bottom_text}"

            # Publish the article in the specified channel
            if post.images_id:
                await self.bot.send_photo(
                    chat_id=channel_id,
                    photo=post.images_id[0],
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
            keyboard = create_original_keyboard(
                article_id, post_index, post.images_search
            )

            # Update the inline keyboard markup of the message
            await query.edit_message_reply_markup(reply_markup=keyboard)
            await query.answer(
                text=f"Published post for article ID: {article_id} in channel: {channel_info.title}"
            )
        except Exception as e:
            print(e)
            await query.answer(text="Something went wrong.")

    async def back_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        query = update.callback_query
        _, article_id, post_index = query.data.split(":", 2)
        post_index = int(post_index)

        article = self.es_repo.get_news_article_by_id(article_id)
        post = article.posts[post_index]

        # Update the inline keyboard markup using the new create_original_keyboard function
        keyboard = create_original_keyboard(article_id, post_index, post.images_search)

        await query.edit_message_reply_markup(reply_markup=keyboard)

    async def handle_post_photo_reply(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        message = update.message
        try:
            if message.reply_to_message.from_user.id == context.bot.id:
                # Get the photo file
                image_id = message.photo[-1].file_id
                message_id = message.reply_to_message.message_id
                print(f"Messsage ID: {message_id} photo ID: {image_id}")

                try:
                    # Retrieve stored article_id and images_search
                    data = context.chat_data.get(message_id)
                    if data:
                        article_id = data.get("article_id")
                        post_index = data.get("post_index")
                        article = self.es_repo.get_news_article_by_id(article_id)
                        article.posts[post_index].images_id = [image_id]
                        self.es_repo.update_news_article(article)
                        await self.send_post(
                            context, message.chat_id, article_id, post_index
                        )
                    else:
                        await message.reply_text(
                            "Something went wrong. Regenerate the post."
                        )
                except Exception as e:
                    print(e)
                    await message.reply_text(
                        "Something went wrongggg. Regenerate the post."
                    )
        except Exception as e:
            print(e)
            await message.reply_text("Something went wrongggg. Regenerate the post.")

    async def handle_text_reply(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        # Get the reply message and the original message it was in reply to
        message = update.message
        try:
            if message.reply_to_message.from_user.id == context.bot.id:
                # Get the photo file
                text = message.text
                message_id = message.reply_to_message.message_id
                print(f"Messsage ID: {message_id} text: {text}")

                try:
                    # Retrieve stored article_id and images_search
                    data = context.chat_data.get(message_id)
                    if data:
                        article_id = data.get("article_id")
                        post_index = data.get("post_index")
                        await self.guidence_post(
                            context, message, article_id, post_index, text
                        )
                    else:
                        await message.reply_text(
                            "Something went wrong. Regenerate the post."
                        )
                except Exception as e:
                    print(e)
                    await message.reply_text(
                        "Something went wrongggg. Regenerate the post."
                    )
        except Exception as e:
            print(e)
            await message.reply_text("Something went wrongggg. Regenerate the post.")


def register(app, bot, repo, es_repo, assistant, search, admin_chat_ids):
    logic = PostHandlers(bot, repo, es_repo, assistant, search, admin_chat_ids)
    app.add_handler(
        CallbackQueryHandler(logic.generate_post_callback, pattern="^generate_post:")
    )
    app.add_handler(
        CallbackQueryHandler(logic.regenerate_post_callback, pattern="^regenerate:")
    )
    app.add_handler(
        CallbackQueryHandler(
            lambda update, context: logic.chosen_variation_callback(update, context, 1),
            pattern="^variation_one:",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            lambda update, context: logic.chosen_variation_callback(update, context, 2),
            pattern="^variation_two:",
        )
    )
    app.add_handler(
        CallbackQueryHandler(logic.make_post_fancy_callback, pattern="^make_fancy:")
    )
    app.add_handler(
        CallbackQueryHandler(logic.publish_menu_callback, pattern="^publish:")
    )
    app.add_handler(
        CallbackQueryHandler(
            logic.publish_to_channel_callback, pattern="^publish_to_channel:"
        )
    )
    app.add_handler(CallbackQueryHandler(logic.back_callback, pattern="^back:"))
    app.add_handler(
        MessageHandler(filters.PHOTO & filters.REPLY, logic.handle_post_photo_reply)
    )
    app.add_handler(
        MessageHandler(filters.TEXT & filters.REPLY, logic.handle_text_reply)
    )
