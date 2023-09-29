import typer
from pydantic import BaseSettings
from rich.console import Console

from channel_automation.assistant.methods import Assistant
from channel_automation.data_access.elasticsearch.methods import ESRepository
from channel_automation.data_access.postgresql.methods import Repository
from channel_automation.search.images import BingImageSearch
from channel_automation.services.bot import TelegramBotService
from channel_automation.services.news_crawler import NewsCrawlerService

app = typer.Typer(
    name="channel-automation",
    help="channel-automation is tool to atomate telegram channels",
    add_completion=False,
)
console = Console()


class Config(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    ADMIN_CHAT_ID: str
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
        config.ADMIN_CHAT_ID,
        repository,
        es_repo,
        assistant,
        image_search,
    )

    telegram_bot_service.run()


@app.command(name="crawler")
def crawler() -> None:
    """Run the crawler."""
    console.print("crawler")
    # Initialize the ElasticsearchNewsArticleRepository with the host and port
    repository = ESRepository(host="localhost", port=9200)

    # Initialize the NewsCrawlerService with the news_article_repository instance
    news_crawler_service = NewsCrawlerService(news_article_repository=repository)

    # Crawl and extract news articles starting from the main page
    main_page = "https://www.bangkokpost.com/travel"
    extracted_articles = news_crawler_service.crawl_and_extract_news_articles(main_page)

    for article in extracted_articles:
        print(f"Title: {article.title}\nDate: {article.date}\n")

    # Schedule the news crawling to run every 30 minutes
    news_crawler_service.schedule_news_crawling(interval_minutes=30)

    # To keep the main thread alive, you can use an infinite loop or use an event to wait
    import time

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.log("Stopping the scheduler...")


if __name__ == "__main__":
    app()
