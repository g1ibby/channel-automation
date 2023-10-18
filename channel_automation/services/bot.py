from typing import List, Optional

from telegram import (
    Bot,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.ext.filters import BaseFilter

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.interfaces.bot_service_interface import ITelegramBotService
from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.interfaces.search_interface import IImageSearch
from channel_automation.models import Admin, ChannelInfo, NewsArticle, Source

AWAITING_SECRET_KEY, EDITING_BUTTON_TEXT = range(2)


class PhotoReplyFilter(BaseFilter):
    def filter(self, message):
        return message.photo is not None and message.reply_to_message is not None


def admin_required(func):
    async def wrapped(
        instance, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        # Check if 'is_admin' is not set in user_data, then determine and set it
        if "is_admin" not in context.user_data:
            await instance.is_user_admin(update, context)

        if not context.user_data.get("is_admin"):
            await update.message.reply_text("You do not have access to this bot.")
            return
        return await func(instance, update, context, *args, **kwargs)

    return wrapped


class TelegramBotService(ITelegramBotService):
    def __init__(
        self,
        token: str,
        repository: IRepository,
        es_repo: IESRepository,
        assistant: IAssistant,
        search: IImageSearch,
    ):
        self.token = token
        self.secret_key = "maled11"
        self.repo = repository
        self.es_repo = es_repo
        self.assistant = assistant
        self.search = search
        self.admin_chat_ids = [admin.user_id for admin in self.repo.get_active_admins()]

    async def is_user_admin(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        user_id = update.effective_user.id
        is_admin = str(user_id) in self.admin_chat_ids
        context.user_data["is_admin"] = is_admin
        return is_admin

    def run(self) -> None:
        app = ApplicationBuilder().token(self.token).build()
        app.add_handler(ChatMemberHandler(self.on_my_chat_member))
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                AWAITING_SECRET_KEY: [
                    MessageHandler(filters.TEXT, self.handle_secret_key)
                ],
            },
            fallbacks=[],
        )
        app.add_handler(conv_handler)

        edit_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.edit_botton_text, pattern="^edit_text:")
            ],
            states={
                EDITING_BUTTON_TEXT: [
                    MessageHandler(filters.TEXT, self.save_channel_botton_text)
                ],
            },
            fallbacks=[],
            per_message=False,
        )
        app.add_handler(edit_conv_handler)
        app.add_handler(CommandHandler("addsource", self.add_source))
        app.add_handler(CommandHandler("disablesource", self.disable_source))
        app.add_handler(CommandHandler("myid", self.get_user_id))

        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.button_press)
        )

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
        app.add_handler(MessageHandler(PhotoReplyFilter(), self.handle_photo_reply))

        app.run_polling()

    async def button_press(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user_input = update.message.text
        if user_input == "Add Source":
            await self.add_source(update, context)
        elif user_input == "Disable Source":
            await self.disable_source(update, context)
        elif user_input == "Active Sources":
            await self.get_active_sources(update, context)
        elif user_input == "My ID":
            await self.get_user_id(update, context)
        elif user_input == "Latest News":
            await self.get_latest_news(update, context)
        elif user_input == "Channels":
            await self.show_channels(update, context)
        else:
            await update.message.reply_text(
                "I'm not sure how to process that. Please select an option from the menu."
            )

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
    def create_start_menu() -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [["Active Sources"], ["Latest News"], ["Channels"]], resize_keyboard=True
        )  # `resize_keyboard=True` makes the keyboard fit the button sizes.

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = str(update.effective_user.id)
        if user_id not in self.admin_chat_ids:
            await update.message.reply_text(
                "Please enter the secret key to access this bot."
            )
            return AWAITING_SECRET_KEY

        keyboard = self.create_start_menu()
        await update.message.reply_text("Welcome to the bot!", reply_markup=keyboard)
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
            keyboard = self.create_start_menu()
            await update.message.reply_text(
                "Welcome to the bot!", reply_markup=keyboard
            )
            return ConversationHandler.END
        else:
            await update.message.reply_text("Incorrect key!")
            return AWAITING_SECRET_KEY

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

    @staticmethod
    def format_news_article(article: NewsArticle) -> str:
        return f"*{article.title}*\n[Read article]({article.source})"

    async def send_formatted_article(
        self,
        chat_ids: list[str],
        article: NewsArticle,
        generate_post_button: bool = True,
    ) -> None:
        bot = Bot(token=self.token)
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
            await bot.send_message(
                chat_id=admin_chat_id,
                text=formatted_article,
                reply_markup=reply_markup,
                parse_mode="Markdown",
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

    async def send_message_to_all_admins(self, message_text: str):
        bot = Bot(token=self.token)
        for admin_chat_id in self.admin_chat_ids:
            await bot.send_message(chat_id=admin_chat_id, text=message_text)

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

            # Send a message to all admins
            message_text = f"I've been added as an admin in the channel: {update.my_chat_member.chat.title}!"
            await self.send_message_to_all_admins(message_text)

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
            images = self.search.search_images(processed_article.images_search, 25)
            processed_article.images_url = images
            self.es_repo.update_news_article(processed_article)

            await query.message.reply_text(
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

    @admin_required
    async def get_latest_news(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        print("Getting latest news...")
        latest_articles = self.es_repo.get_latest_news(10)
        if not latest_articles:
            await update.message.reply_text("No articles found.")
            return

        for article in latest_articles:
            await self.send_formatted_article(
                [update.effective_chat.id], article, generate_post_button=True
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
        await self.send_formatted_article(self.admin_chat_ids, article)

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
