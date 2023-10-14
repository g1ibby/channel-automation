from typing import Any

import asyncio
import datetime
from dataclasses import fields

import pytz
from apscheduler.schedulers.background import BackgroundScheduler

from channel_automation.data_access.elasticsearch.methods import ESRepository
from channel_automation.data_access.postgresql.methods import Repository
from channel_automation.interfaces.bot_service_interface import ITelegramBotService
from channel_automation.interfaces.news_crawler_service_interface import (
    INewsCrawlerService,
)
from channel_automation.models import NewsArticle
from channel_automation.services.crawler.sources.bangkokpost import BangkokpostCrawler
from channel_automation.services.crawler.sources.common import CommonCrawler
from channel_automation.services.crawler.sources.tatnews import TatnewsCrawler
from channel_automation.services.crawler.sources.tourismthailand import (
    TourismthailandCrawler,
)


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
        self.scheduler = BackgroundScheduler(timezone=bangkok_tz)
        self.scheduler.start()

    def start_crawling(self):
        self.refresh_sources()
        self.scheduler.add_job(
            self.refresh_sources,
            "interval",
            hours=1,
        )

    def schedule_news_crawling(self, url: str):
        print(f"Running crawling for {url}")

        async def run_crawl():  # Define a new async function
            await self.crawl_and_extract_news_articles(
                url
            )  # Call your async method here

        loop = asyncio.new_event_loop()  # Create a new event loop
        asyncio.set_event_loop(loop)  # Set the new event loop as the current event loop

        self.scheduler.add_job(
            loop.run_until_complete,
            args=[run_crawl()],  # Pass the new async function call
            next_run_time=datetime.datetime.now(),
        )
        self.scheduler.add_job(
            loop.run_until_complete,
            "interval",
            hours=6,
            args=[run_crawl()],  # Pass the new async function call
            replace_existing=True,
        )

        print(f"Scheduled crawling for {url}")

    async def crawl_and_extract_news_articles(self, main_page: str):
        print(f"crawl and extract {main_page}")
        extracted_articles = []
        if "bangkokpost.com" in main_page:
            crawler = BangkokpostCrawler()
            extracted_articles = crawler.crawl()
        elif "tatnews.org" in main_page:
            crawler = TatnewsCrawler()
            extracted_articles = crawler.crawl()
        elif "tourismthailand.org" in main_page:
            crawler = TourismthailandCrawler()
            extracted_articles = crawler.crawl()
        else:
            common_crawler = CommonCrawler(main_page)
            extracted_articles = common_crawler.crawl()

        for article in extracted_articles:
            a = self.news_article_repository.save_news_article(article)
            if a is not None:
                await self.bot_service.send_article_to_admin(article)
        return None

    def refresh_sources(self):
        current_sources = {job.args[0] for job in self.scheduler.get_jobs()}
        print(current_sources)
        new_sources = {s.link for s in self.repo.get_active_sources()}
        # new_sources = set(self.repo.get_active_sources())
        print(new_sources)

        # Schedule new sources
        for source in new_sources - current_sources:
            self.schedule_news_crawling(source)

        # Remove disabled sources
        for source in current_sources - new_sources:
            self.scheduler.remove_job(source)
