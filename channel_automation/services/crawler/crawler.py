from typing import Any

from dataclasses import fields

from apscheduler.schedulers.background import BackgroundScheduler

from channel_automation.data_access.elasticsearch.methods import ESRepository
from channel_automation.data_access.postgresql.methods import Repository
from channel_automation.interfaces.news_crawler_service_interface import (
    INewsCrawlerService,
)
from channel_automation.models import NewsArticle
from channel_automation.services.crawler.sources.bangkokpost import BangkokpostCrawler
from channel_automation.services.crawler.sources.common import CommonCrawler


class NewsCrawlerService:
    def __init__(self, news_article_repository: ESRepository, repo: Repository):
        self.news_article_repository = news_article_repository
        self.repo = repo
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.scheduler.add_job(
            self.refresh_sources,
            "interval",
            hours=1,
        )

    def start_crawling(self):
        sources = self.repo.get_active_sources()
        for source in sources:
            self.schedule_news_crawling(source.link)

    def schedule_news_crawling(self, url: str):
        self.scheduler.add_job(
            self.crawl_and_extract_news_articles,
            "interval",
            hours=6,
            args=[url],
            replace_existing=True,
        )
        print(f"Scheduled crawling for {url}")

    def crawl_and_extract_news_articles(self, main_page: str):
        extracted_articles = []
        if "bangkokpost.com" in main_page:
            crawler = BangkokpostCrawler()
            extracted_articles = crawler.crawl()
        else:
            common_crawler = CommonCrawler(main_page)
            extracted_articles = common_crawler.crawl()

        for article in extracted_articles:
            self.news_article_repository.save_news_article(article)
        return None

    def refresh_sources(self):
        current_sources = {job.args[0] for job in self.scheduler.get_jobs()}
        new_sources = set(self.repo.get_active_sources())

        # Schedule new sources
        for source in new_sources - current_sources:
            self.schedule_news_crawling(source.link)

        # Remove disabled sources
        for source in current_sources - new_sources:
            self.scheduler.remove_job(source)
