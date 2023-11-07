from typing import List, Optional

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base_web_crawler import BaseWebCrawler


class CNNTravelNewsCrawler(BaseWebCrawler):
    BASE_URL = "https://edition.cnn.com/"

    def __init__(self) -> None:
        super().__init__(f"{CNNTravelNewsCrawler.BASE_URL}travel/news")

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        if not html_content:
            return []
        soup = BeautifulSoup(html_content, "html.parser")
        links = []
        articles = soup.find_all(
            "a",
            class_="container__link container__link--type-article container_vertical-strip__link",
        )
        for link in articles:
            full_link = urljoin(self.BASE_URL, link["href"])
            links.append(full_link)
        return links

    def extract_main_image(self, html_content: Optional[str]) -> Optional[str]:
        if not html_content:
            return None
        soup = BeautifulSoup(html_content, "html.parser")
        # First, try to find the image using the 'data-url' attribute in the first variation
        div_tag = soup.find("div", {"data-url": True, "class": "image"})
        if div_tag:
            return div_tag["data-url"]

        # If the first method fails, look for the 'img' tag directly as in the second variation
        img_tag = soup.find("img", {"class": "image__dam-img"})
        if img_tag and "src" in img_tag.attrs:
            return img_tag["src"]
        return None
