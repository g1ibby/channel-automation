from typing import Optional

from bs4 import BeautifulSoup

from .base_web_crawler import BaseWebCrawler


class PattayaPeopleNewsCrawler(BaseWebCrawler):
    def __init__(self) -> None:
        super().__init__("https://pattayapeople.ru/news/")

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        if not html_content:
            return []
        soup = BeautifulSoup(html_content, "html.parser")
        news_links = []
        for link in soup.find_all("a"):
            if link.has_attr("href") and "/news/" in link["href"]:
                news_links.append(link["href"])
        return news_links

    def extract_main_image(self, html_content: Optional[str]) -> Optional[str]:
        if not html_content:
            return None
        soup = BeautifulSoup(html_content, "html.parser")
        main_image_div = soup.find(
            "div", class_="entry-image post-card post-card__thumbnail"
        )
        if main_image_div:
            main_image = main_image_div.find("img")
            if main_image and main_image.has_attr("src"):
                return main_image["src"]
        return None
