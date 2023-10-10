from typing import Any, Optional

import json
from dataclasses import fields

import requests
import trafilatura
from bs4 import BeautifulSoup

from channel_automation.models import NewsArticle


def news_article_from_json(json_data: dict[str, Any]) -> NewsArticle:
    init_args = {
        field.name: json_data.get(field.metadata.get("json_key", field.name))
        for field in fields(NewsArticle)
    }
    return NewsArticle(**init_args)


class TatnewsCrawler:
    def __init__(self) -> None:
        pass

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
        news_links = []
        url = "https://www.tatnews.org/category/thailand-tourism-news/"
        response = requests.get(url)
        if response:
            print(f"Response: {response.status_code}")
            lnks = self.extract_news_links(response.text)
            news_links.extend(lnks)

        return news_links

    def extract_news_links(self, html_content):
        # Initialize a BeautifulSoup object
        soup = BeautifulSoup(html_content, "html.parser")

        # Initialize an empty list to store the news links
        specific_news_links = []

        # Find and loop through each news item
        for news_item in soup.find_all("h2", class_="post-title"):
            link = news_item.find("a")["href"]
            specific_news_links.append(link)

        return specific_news_links

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
