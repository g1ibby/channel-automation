from typing import Optional

import json
import time

from channel_automation.models import NewsArticle

from .base_web_crawler import BaseWebCrawler

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


class TourismthailandCrawler(BaseWebCrawler):
    def __init__(self) -> None:
        super().__init__(
            base_url="https://www.tourismthailand.org",
            headers=headers,
        )

    async def fetch_json_from_api(self, url: str) -> dict:
        timestamp = str(int(time.time() * 1000))
        full_url = f"{url}&timestamp={timestamp}"
        json_content = await self.fetch(full_url)
        return json.loads(json_content) if json_content else {}

    async def get_tourismthailand_breaking_news_links(self) -> list[str]:
        url = "https://api.tourismthailand.org/api/home/get_breaking_news?Language=en"
        parsed_json = await self.fetch_json_from_api(url)
        return [news["url"] for news in parsed_json.get("result", [])]

    async def get_tourismthailand_announcement_links(self) -> list[str]:
        url = (
            "https://api.tourismthailand.org/api/home/get_news_announcement?Language=en"
        )
        parsed_json = await self.fetch_json_from_api(url)
        return [
            f"https://www.tourismthailand.org/Articles/{announcement['slug']}"
            for announcement in parsed_json.get("result", [])
        ]

    async def crawl(self) -> list[NewsArticle]:
        data1 = await self.get_tourismthailand_breaking_news_links()
        data2 = await self.get_tourismthailand_announcement_links()

        print(f"Found {len(data1)} breaking news articles")
        print(f"Found {len(data2)} announcement articles")
        return await self.extract_articles(data1 + data2)

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        return []

    def extract_main_image(self, html_content: Optional[str]) -> Optional[str]:
        return None
