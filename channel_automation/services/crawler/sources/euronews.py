from typing import Callable, Optional

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base_web_crawler import BaseWebCrawler


class EuronewsTourismCrawler(BaseWebCrawler):
    BASE_URL = "https://www.euronews.com"

    def __init__(self, base_url: str) -> None:
        super().__init__(base_url)
        self.filters: list[Callable[[str], bool]] = [
            lambda url: "/live-news/" not in url  # you can add more filters here
        ]

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        if not html_content:
            return []
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(html_content, "lxml")
        # Initialize an empty list to store the scraped article URLs
        article_links = []
        # Find all 'article' elements within the div class "o-block-listing__articles"
        articles = soup.find("div", {"class": "o-block-listing__articles"}).find_all(
            "article"
        )
        # Loop through each 'article' element and extract the article URL
        for article in articles:
            a_tag = article.find("a", {"class": "media__img__link"})
            if a_tag:
                article_url = a_tag.get("href")
                # Add the prefix to each article URL
                full_link = urljoin(self.BASE_URL, article_url)
                article_links.append(full_link)

        return article_links

    def extract_main_image(self, html_content: Optional[str]) -> Optional[str]:
        # Parse the HTML content
        soup = BeautifulSoup(html_content, "lxml")
        # Find the img tag within the class "c-article-image-video"
        img_tag = soup.select_one(
            ".c-article-image-video .js-poster-img.c-article-media__img"
        )
        # If img tag exists and has 'src' attribute, return the URL
        if img_tag and "src" in img_tag.attrs:
            return img_tag["src"]
        return None
