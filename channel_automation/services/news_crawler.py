from typing import Any, Dict, List, Optional

import json
from dataclasses import fields

import trafilatura
from trafilatura.spider import focused_crawler

from channel_automation.data_access.elasticsearch.methods import ESRepository
from channel_automation.interfaces.news_crawler_service_interface import (
    INewsCrawlerService,
)
from channel_automation.models import NewsArticle


def news_article_from_json(json_data: dict[str, Any]) -> NewsArticle:
    init_args = {
        field.name: json_data.get(field.metadata.get("json_key", field.name))
        for field in fields(NewsArticle)
    }
    return NewsArticle(**init_args)


class NewsCrawlerService(INewsCrawlerService):
    def __init__(self, news_article_repository: ESRepository):
        self.news_article_repository = news_article_repository

    def crawl_and_extract_news_articles(self, main_page: str) -> list[NewsArticle]:
        todo, known_links = focused_crawler(
            main_page, max_seen_urls=2, max_known_urls=100
        )
        news_links = [link for link in known_links if self.news_links_filter(link)]
        extracted_articles = []

        for link in news_links:
            article = self.extract_content(link)
            if article:
                self.news_article_repository.save_news_article(article)
                extracted_articles.append(article)

        return extracted_articles

    def news_links_filter(self, url: str) -> bool:
        return (
            url.startswith("https://www.bangkokpost.com/travel/") and "/travel/" in url
        )

    def extract_content(self, url: str) -> Optional[NewsArticle]:
        downloaded = trafilatura.fetch_url(url)

        try:
            extracted_data = trafilatura.extract(
                downloaded,
                include_comments=False,
                with_metadata=True,
                favor_precision=True,
                deduplicate=True,
                output_format="json",
            )
            if extracted_data is not None:
                data = json.loads(extracted_data)
                article = news_article_from_json(data)
                return article
        except Exception as e:
            print(f"Error extracting content: {e}")

        return None

    def schedule_news_crawling(self, interval_minutes: int = 30) -> None:
        # You can use a scheduler like APScheduler to run the crawling process periodically
        # The example below uses the BackgroundScheduler from APScheduler
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler()
        scheduler.add_job(
            self.crawl_and_extract_news_articles,
            "interval",
            minutes=interval_minutes,
            args=["https://www.bangkokpost.com/travel/"],
        )
        scheduler.start()
