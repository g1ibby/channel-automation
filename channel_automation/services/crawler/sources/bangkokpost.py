from typing import Optional

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base_web_crawler import BaseWebCrawler

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "X-Requested-With": "XMLHttpRequest",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": "https://www.bangkokpost.com/life/travel",
    "Cookie": "is_pdpa=1; bkp_survey=1; is_gdpr=1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


class BangkokpostCrawler(BaseWebCrawler):
    BASE_URL = "https://www.bangkokpost.com/"

    def __init__(self) -> None:
        super().__init__(base_url=f"{BangkokpostCrawler.BASE_URL}", headers=headers)

    async def crawl_news_links(self) -> list[str]:
        news_links = []
        for page in range(1, 2):
            url = f"{self.base_url}v3/list_content/life/travel?page={page}"
            html_content = await self.fetch(url)
            if html_content:
                lnks = self.extract_news_links(html_content)
                news_links.extend(lnks)
        return news_links

    def extract_news_links(self, html_content: str) -> list[str]:
        soup = BeautifulSoup(html_content, "html.parser")
        specific_news_links = []
        for news_item in soup.find_all("div", class_="news--list boxnews-horizon"):
            link_tag = news_item.find("figure").find("a", href=True)
            if link_tag is not None:
                full_link = urljoin(self.BASE_URL, link_tag["href"])
                specific_news_links.append(full_link)
        return specific_news_links

    def extract_main_image(self, html_content: str) -> Optional[str]:
        # Implement this method if necessary, or return None if main image extraction is not applicable
        return None
