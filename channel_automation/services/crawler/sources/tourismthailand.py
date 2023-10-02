from typing import Any, List, Optional

import json
import time
from dataclasses import fields

import trafilatura
from requests import get

from channel_automation.models import NewsArticle


def news_article_from_json(json_data: dict[str, Any]) -> NewsArticle:
    init_args = {
        field.name: json_data.get(field.metadata.get("json_key", field.name))
        for field in fields(NewsArticle)
    }
    return NewsArticle(**init_args)


headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Language": "en",
    "Origin": "https://www.tourismthailand.org",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": "https://www.tourismthailand.org/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


class TourismthailandCrawler:
    def fetch_json_from_api(self, url: str) -> dict:
        timestamp = str(int(time.time() * 1000))
        full_url = f"{url}&timestamp={timestamp}"
        response = get(full_url, headers=headers)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            print(f"Error: {response.status_code}")
            return {}

    def get_tourismthailand_breaking_news_links(self) -> list[str]:
        url = "https://api.tourismthailand.org/api/home/get_breaking_news?Language=en"
        parsed_json = self.fetch_json_from_api(url)
        return [news["url"] for news in parsed_json["result"]]

    def get_tourismthailand_announcement_links(self) -> list[str]:
        url = (
            "https://api.tourismthailand.org/api/home/get_news_announcement?Language=en"
        )
        parsed_json = self.fetch_json_from_api(url)
        return [
            f"https://www.tourismthailand.org/Articles/{announcement['slug']}"
            for announcement in parsed_json["result"]
        ]

    def crawl(self) -> list[NewsArticle]:
        extracted_articles = []
        data1 = self.get_tourismthailand_breaking_news_links()
        data2 = self.get_tourismthailand_announcement_links()

        for result in data1 + data2:
            article = self.extract_content(result)
            if article:
                extracted_articles.append(article)

        return extracted_articles

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
