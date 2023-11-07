from typing import Optional

import re

from bs4 import BeautifulSoup

from .base_web_crawler import BaseWebCrawler


class ThepattayaNewsCrawler(BaseWebCrawler):
    def __init__(self) -> None:
        super().__init__(
            base_url="https://thepattayanews.com/",
        )

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        soup = BeautifulSoup(html_content, "html.parser")
        specific_news_links = []

        for div in soup.find_all("h3", {"class": re.compile("td-module-title")}):
            for a in div.find_all("a", href=True):
                specific_news_links.append(a["href"])

        return specific_news_links

    def extract_main_image(self, html_content: Optional[str]) -> str:
        soup = BeautifulSoup(html_content, "html.parser")
        img_tag = soup.select_one("div.td-post-featured-image img")
        if img_tag and "src" in img_tag.attrs:
            return img_tag["src"]
        return None
