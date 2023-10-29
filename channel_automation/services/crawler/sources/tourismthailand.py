from typing import Optional

import json
import time

import aiohttp
import trafilatura
from tenacity import retry, stop_after_attempt, wait_random_exponential

from channel_automation.models import NewsArticle

from ..utils import news_article_from_json

timeout = aiohttp.ClientTimeout(total=15)
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


@retry(
    stop=stop_after_attempt(5),
    wait=wait_random_exponential(multiplier=1, min=3, max=30),
)
async def fetch_json_from_api_with_retry(session, url: str, headers) -> dict:
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"Error: {response.status}")
            return {}


class TourismthailandCrawler:
    async def fetch_json_from_api(self, url: str) -> dict:
        timestamp = str(int(time.time() * 1000))
        full_url = f"{url}&timestamp={timestamp}"
        async with aiohttp.ClientSession(timeout=timeout) as session:
            return await fetch_json_from_api_with_retry(session, full_url, headers)

    async def get_tourismthailand_breaking_news_links(self) -> list[str]:
        url = "https://api.tourismthailand.org/api/home/get_breaking_news?Language=en"
        parsed_json = await self.fetch_json_from_api(url)
        return [news["url"] for news in parsed_json["result"]]

    async def get_tourismthailand_announcement_links(self) -> list[str]:
        url = (
            "https://api.tourismthailand.org/api/home/get_news_announcement?Language=en"
        )
        parsed_json = await self.fetch_json_from_api(url)
        return [
            f"https://www.tourismthailand.org/Articles/{announcement['slug']}"
            for announcement in parsed_json["result"]
        ]

    async def crawl(self) -> list[NewsArticle]:
        extracted_articles = []
        data1 = await self.get_tourismthailand_breaking_news_links()
        data2 = await self.get_tourismthailand_announcement_links()

        print(f"Found {len(data1)} breaking news articles")
        print(f"Found {len(data2)} announcement articles")
        for result in data1 + data2:
            article = await self.extract_content(result)
            if article:
                extracted_articles.append(article)

        return extracted_articles

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_random_exponential(multiplier=1, min=3, max=30),
    )
    async def extract_content(self, url: str) -> Optional[NewsArticle]:
        print(f"Extracting content from {url}")
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    downloaded = await response.read()
                    try:
                        extracted_data = trafilatura.extract(
                            downloaded,
                            include_comments=False,
                            with_metadata=True,
                            favor_precision=True,
                            deduplicate=True,
                            output_format="json",
                        )
                        if extracted_data:
                            data = json.loads(extracted_data)
                            article = await news_article_from_json(data)
                            article.images_url = []
                            return article
                    except Exception as e:
                        print(f"Error extracting content: {e}")

        return None
