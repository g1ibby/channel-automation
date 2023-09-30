from typing import Any, Dict, List, Optional

import json
from dataclasses import fields

import trafilatura
from requests import request
from trafilatura.spider import focused_crawler

from channel_automation.models import NewsArticle, news


def news_article_from_json(json_data: dict[str, Any]) -> NewsArticle:
    init_args = {
        field.name: json_data.get(field.metadata.get("json_key", field.name))
        for field in fields(NewsArticle)
    }
    return NewsArticle(**init_args)


class CommonCrawler:
    def __init__(self, url: str) -> None:
        self.url = url

    def crawl(self) -> list[NewsArticle]:
        news_links = self.crawl_news_links()
        extracted_articles = []
        for link in news_links:
            print(f"Extracting content from {link}")
            article = self.extract_content(link)
            if article:
                extracted_articles.append(article)

        return extracted_articles

    def crawl_news_links(self) -> list[str]:
        todo, known_links = focused_crawler(
            self.url, max_seen_urls=2, max_known_urls=100
        )
        print(f"Found {len(known_links)} new links")
        news_links = [link for link in known_links if self.news_links_filter(link)]
        return news_links

    def news_links_filter(self, link: str) -> bool:
        return True

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
