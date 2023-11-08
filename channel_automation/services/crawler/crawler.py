import datetime
import logging

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from channel_automation.data_access.elasticsearch.methods import ESRepository
from channel_automation.data_access.postgresql.methods import Repository
from channel_automation.interfaces.bot_service_interface import ITelegramBotService
from channel_automation.services.crawler.sources.bangkokpost import BangkokpostCrawler
from channel_automation.services.crawler.sources.clubbingthailand import (
    ClubbingThailandCrawler,
)
from channel_automation.services.crawler.sources.cnn import CNNTravelNewsCrawler
from channel_automation.services.crawler.sources.euronews import EuronewsTourismCrawler
from channel_automation.services.crawler.sources.ria import RiaNewsCrawler
from channel_automation.services.crawler.sources.tatnews import TatnewsCrawler
from channel_automation.services.crawler.sources.thepattayanews import (
    ThepattayaNewsCrawler,
)
from channel_automation.services.crawler.sources.thephuketnews import PhuketNewsCrawler
from channel_automation.services.crawler.sources.thethaiger import ThethaigerNewsCrawler
from channel_automation.services.crawler.sources.tourismthailand import (
    TourismthailandCrawler,
)

# Initialize logging
logging.basicConfig()
# Set the log level for APScheduler to DEBUG
logging.getLogger("apscheduler").setLevel(logging.DEBUG)


class NewsCrawlerService:
    def __init__(
        self,
        news_article_repository: ESRepository,
        repo: Repository,
        bot_service: ITelegramBotService,
    ):
        self.news_article_repository = news_article_repository
        self.repo = repo
        self.bot_service = bot_service
        bangkok_tz = pytz.timezone("Asia/Bangkok")
        self.scheduler = AsyncIOScheduler(timezone=bangkok_tz)
        self.scheduler.start()

    async def start_crawling(self):
        self.scheduler.add_job(
            self.refresh_sources,
            "interval",
            hours=1,
            next_run_time=datetime.datetime.now(),
        )

    async def schedule_news_crawling(self, url: str):
        print(f"Running crawling for {url}")

        self.scheduler.add_job(
            self.crawl_and_extract_news_articles,
            "interval",
            hours=6,
            args=[url],
            next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=10),
            coalesce=True,
            max_instances=6,
            misfire_grace_time=20,
        )

        print(f"Scheduled crawling for {url}")

    async def crawl_and_extract_news_articles(self, main_page: str):
        print(f"Crawling and extracting articles from {main_page}")
        extracted_articles = []
        crawler_class = None

        # Map domain names to crawler classes
        crawler_map = {
            "bangkokpost.com": BangkokpostCrawler,
            "tatnews.org": TatnewsCrawler,
            "tourismthailand.org": TourismthailandCrawler,
            "thepattayanews.com": ThepattayaNewsCrawler,
            "thethaiger.com": ThethaigerNewsCrawler,
            "https://www.euronews.com/tag/tourism": lambda: EuronewsTourismCrawler(
                "https://www.euronews.com/tag/tourism"
            ),
            "https://www.euronews.com/tag/digital-nomad": lambda: EuronewsTourismCrawler(
                "https://www.euronews.com/tag/digital-nomad"
            ),
            "thephuketnews.com": PhuketNewsCrawler,
            "clubbingthailand.com": ClubbingThailandCrawler,
            "https://edition.cnn.com/travel/news": CNNTravelNewsCrawler,
            "https://ria.ru/tourism_news": lambda: RiaNewsCrawler(
                "https://ria.ru/tourism_news/"
            ),
            "https://ria.ru/location_Thailand": lambda: RiaNewsCrawler(
                "https://ria.ru/location_Thailand/"
            ),
        }

        # Find the appropriate crawler class based on the main_page URL
        for domain, crawler_cls in crawler_map.items():
            if domain in main_page:
                crawler_class = crawler_cls
                break

        if crawler_class is None:
            print(f"Unknown source: {main_page}")
            return None

        # Use the crawler class with an async context manager
        async with crawler_class() as crawler:
            extracted_articles = await crawler.crawl()
            for article in extracted_articles:
                a = self.news_article_repository.save_news_article(article)
                if a is not None:
                    await self.bot_service.send_article_to_admin(article)

    async def refresh_sources(self):
        print("Refreshing sources...")
        current_sources = {
            job.args[0] for job in self.scheduler.get_jobs() if len(job.args) == 1
        }
        new_sources = {s.link for s in self.repo.get_active_sources()}

        # Schedule new sources
        for source in new_sources - current_sources:
            await self.schedule_news_crawling(source)

        # Remove disabled sources
        for source in current_sources - new_sources:
            self.scheduler.remove_job(source)
