from typing import Callable, Optional

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base_web_crawler import BaseWebCrawler


class TourpromNewsCrawler(BaseWebCrawler):
    BASE_URL = "https://www.tourprom.ru"

    def __init__(self, base_url: str) -> None:
        super().__init__(base_url)

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        if not html_content:
            return []
        soup = BeautifulSoup(html_content, "html.parser")
        news_links = []
        for a in soup.find_all("a", class_="news-block__text link-more"):
            link = urljoin(self.BASE_URL, a["href"])
            news_links.append(link)

        return news_links

    def extract_main_image(self, html_content: Optional[str]) -> Optional[str]:
        if not html_content:
            return None
        soup = BeautifulSoup(html_content, "html.parser")
        image_div = soup.find("div", class_="photo-wrap")
        if image_div:
            image_tag = image_div.find("img")
            if image_tag and "src" in image_tag.attrs:
                image_url = image_tag["src"]
                # Make sure the image URL is absolute
                image_url = urljoin(self.base_url, image_url)
                return image_url
        return None
