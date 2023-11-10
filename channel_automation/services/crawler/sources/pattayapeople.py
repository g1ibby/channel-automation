from typing import Optional

from bs4 import BeautifulSoup

from .base_web_crawler import BaseWebCrawler


class PattayaPeopleNewsCrawler(BaseWebCrawler):
    BASE_URL = "https://pattayapeople.ru/news"

    def __init__(self) -> None:
        super().__init__(PattayaPeopleNewsCrawler.BASE_URL)

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        if not html_content:
            return []
        soup = BeautifulSoup(html_content, "html.parser")
        news_links = []
        # Ensure we have a consistent base URL with a trailing slash for comparison.
        base_url = self.BASE_URL.rstrip("/") + "/"
        for link in soup.find_all("a"):
            href = link.get("href", "")
            # Normalize href for comparison by ensuring it has a trailing slash
            normalized_href = href.rstrip("/") + "/"
            # Check if 'href' starts with BASE_URL, is not exactly BASE_URL or BASE_URL/ (excluding base link),
            # and does not continue with '/page/' indicating a pagination link.
            if (
                normalized_href.startswith(base_url)
                and normalized_href != base_url
                and not normalized_href[len(base_url) :].startswith("page/")
            ):
                # Append original href, not normalized, to maintain original URL format
                news_links.append(href)
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
