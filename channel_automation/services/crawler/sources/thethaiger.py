from typing import Callable, Optional

from bs4 import BeautifulSoup

from .base_web_crawler import BaseWebCrawler


class ThethaigerNewsCrawler(BaseWebCrawler):
    def __init__(self) -> None:
        super().__init__("https://thethaiger.com/news")
        self.filters: list[Callable[[str], bool]] = [
            lambda url: "/live-news/" not in url
        ]

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        if not html_content:
            return []
        soup = BeautifulSoup(html_content, "html.parser")
        links_elements = soup.select(".post-item")
        news_links = [element.find("a")["href"] for element in links_elements]
        return news_links

    def extract_main_image(self, html_content: Optional[str]) -> Optional[str]:
        soup = BeautifulSoup(html_content, "html.parser")
        figure_tag = soup.select_one(
            ".featured-area .featured-area-inner .single-featured-image img"
        )
        if figure_tag and "src" in figure_tag.attrs:
            return figure_tag["src"]
        return None
