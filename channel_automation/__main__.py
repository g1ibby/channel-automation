import asyncio

import typer
from pydantic import BaseSettings
from rich.console import Console

from channel_automation.assistant.methods import Assistant
from channel_automation.data_access.elasticsearch.methods import ESRepository
from channel_automation.data_access.postgresql.methods import Repository
from channel_automation.search.images import BingImageSearch
from channel_automation.services.bot.bot import TelegramBotService
from channel_automation.services.crawler.crawler import NewsCrawlerService

app = typer.Typer(
    name="channel-automation",
    help="channel-automation is tool to atomate telegram channels",
    add_completion=False,
)
console = Console()


class Config(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    DATABASE_URL: str = "postgresql://user:password@localhost/automation"
    ES_HOST: str = "localhost"
    ES_PORT: int = 9200
    ASSISTANT_TOKEN: str

    class Config:
        env_prefix = "APP_"


@app.command(name="bot")
def bot() -> None:
    """Run the bot."""
    config = Config()

    repository = Repository(config.DATABASE_URL)
    es_repo = ESRepository(host=config.ES_HOST, port=config.ES_PORT)
    assistant = Assistant(config.ASSISTANT_TOKEN)
    image_search = BingImageSearch()
    telegram_bot_service = TelegramBotService(
        config.TELEGRAM_BOT_TOKEN,
        repository,
        es_repo,
        assistant,
        image_search,
    )
    # print("Starting the crawler...")
    # news_crawler_service = NewsCrawlerService(es_repo, repository, telegram_bot_service)
    # news_crawler_service.start_crawling()

    print("Starting the bot...")
    telegram_bot_service.run()


@app.command(name="crawler")
def crawler() -> None:
    """Run the crawler."""
    config = Config()

    es_repo = ESRepository(host=config.ES_HOST, port=config.ES_PORT)
    repo = Repository(config.DATABASE_URL)
    assistant = Assistant(config.ASSISTANT_TOKEN)
    image_search = BingImageSearch()
    telegram_bot_service = TelegramBotService(
        config.TELEGRAM_BOT_TOKEN,
        repo,
        es_repo,
        assistant,
        image_search,
    )
    asyncio.run(crawler_logic(es_repo, repo, telegram_bot_service))


async def crawler_logic(es_repo, repo, telegram_bot_service):
    news_crawler_service = NewsCrawlerService(es_repo, repo, telegram_bot_service)
    await news_crawler_service.start_crawling()

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    app()
