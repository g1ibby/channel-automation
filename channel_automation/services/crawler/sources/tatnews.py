from typing import Optional

from bs4 import BeautifulSoup

from .base_web_crawler import BaseWebCrawler


class TatnewsCrawler(BaseWebCrawler):
    def __init__(self) -> None:
        super().__init__(
            base_url="https://www.tatnews.org/category/thailand-tourism-news/",
        )

    def extract_news_links(self, html_content: Optional[str]):
        soup = BeautifulSoup(html_content, "html.parser")
        specific_news_links = []
        # Find and loop through each news item
        for news_item in soup.find_all("h2", class_="post-title"):
            link = news_item.find("a")["href"]
            specific_news_links.append(link)

        return specific_news_links

    def extract_main_image(self, html_content: Optional[str]) -> Optional[str]:
        return None
