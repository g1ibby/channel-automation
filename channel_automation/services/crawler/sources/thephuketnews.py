from typing import Optional

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base_web_crawler import BaseWebCrawler

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "DNT": "1",
    "Connection": "keep-alive",
    "Cookie": "PHPSESSID=e9ced6913e0a79c782afcf59d242aafe",
    "Upgrade-Insecure-Requests": "1",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


class PhuketNewsCrawler(BaseWebCrawler):
    BASE_URL = "https://www.thephuketnews.com/"

    def __init__(self) -> None:
        super().__init__(
            urljoin(PhuketNewsCrawler.BASE_URL, "/sport-thailand.php"), headers
        )

    def extract_news_links(self, html_content: Optional[str]) -> list[str]:
        if not html_content:
            return []
        soup = BeautifulSoup(html_content, "html.parser")
        links = []
        for item in soup.select(".row.p-2.border-bottom"):
            link = item.select_one("h5 a")["href"]
            full_link = urljoin(self.BASE_URL, link)
            links.append(full_link)
        return links

    def extract_main_image(self, html_content: Optional[str]) -> Optional[str]:
        soup = BeautifulSoup(html_content, "html.parser")
        img_tag = soup.find("img", {"class": "img-fluid"})
        if img_tag and "src" in img_tag.attrs:
            relative_url = img_tag["src"]
            # Convert the relative URL to an absolute URL
            absolute_url = urljoin(self.BASE_URL, relative_url)
            return absolute_url
        return None
