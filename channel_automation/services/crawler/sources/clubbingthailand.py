from typing import Optional

from bs4 import BeautifulSoup

from .base_web_crawler import BaseWebCrawler


class ClubbingThailandCrawler(BaseWebCrawler):
    def __init__(self) -> None:
        super().__init__(base_url="https://clubbingthailand.com/")

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        news_links = []
        if not html_content:
            return news_links
        soup = BeautifulSoup(html_content, "html.parser")
        for item in soup.select(".pt-cv-content-item"):
            link = item.select_one("a.pt-cv-href-thumbnail")
            if link:
                news_links.append(link["href"])
        return news_links

    def extract_main_image(self, html_content: Optional[str]) -> Optional[str]:
        soup = BeautifulSoup(html_content, "html.parser")

        figure_tag = soup.select_one("div.wp-block-image figure.aligncenter a")
        if figure_tag and "href" in figure_tag.attrs:
            return figure_tag["href"]
        return None
