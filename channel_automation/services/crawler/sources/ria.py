from typing import Optional

from bs4 import BeautifulSoup

from .base_web_crawler import BaseWebCrawler


class RiaNewsCrawler(BaseWebCrawler):
    def __init__(self, base_url: str) -> None:
        super().__init__(base_url)

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        article_links = soup.find_all("a", class_="list-item__title")
        news_links = [
            link["href"] for link in article_links if link and "href" in link.attrs
        ]
        return news_links

    def extract_main_image(self, html_content: Optional[str]) -> Optional[str]:
        if not html_content:
            return None

        soup = BeautifulSoup(html_content, "html.parser")
        image_container = soup.find("div", class_="photoview__open")
        if image_container:
            main_image_src = image_container.find("img")
            if main_image_src and "src" in main_image_src.attrs:
                return main_image_src["src"]
        return None
