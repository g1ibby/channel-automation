from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext.filters import BaseFilter


class PhotoReplyFilter(BaseFilter):
    def filter(self, message):
        print(message)
        return (
            message.photo is not None
            and message.reply_to_message is not None
            and message.text is None
        )


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
