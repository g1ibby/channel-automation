from telegram import Bot, Update
from telegram.ext import ContextTypes

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.interfaces.search_interface import IImageSearch


class BaseHandlers:
    def __init__(
        self,
        bot: Bot,
        repo: IRepository,
        es_repo: IESRepository,
        assistant: IAssistant,
        search: IImageSearch,
        admin_chat_ids: list,
    ) -> None:
        self.bot = bot
        self.secret_key = "maled11"
        self.repo = repo
        self.es_repo = es_repo
        self.assistant = assistant
        self.search = search
        self.admin_chat_ids = admin_chat_ids

    async def is_user_admin(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        user_id = update.effective_user.id
        is_admin = str(user_id) in self.admin_chat_ids
        context.user_data["is_admin"] = is_admin
        return is_admin

    async def send_message_to_all_admins(self, message_text: str):
        for admin_chat_id in self.admin_chat_ids:
            await self.bot.send_message(chat_id=admin_chat_id, text=message_text)
