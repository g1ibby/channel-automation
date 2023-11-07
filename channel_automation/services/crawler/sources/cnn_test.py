from typing import Callable, List, Optional

from urllib.parse import urljoin

import aiohttp
import trafilatura
from bs4 import BeautifulSoup
from lxml import html

base_url = "https://edition.cnn.com/"


def extract_news_links(html_content: Optional[str]) -> list[str]:
    if not html_content:
        return []
    soup = BeautifulSoup(html_content, "html.parser")
    links = []
    articles = soup.find_all(
        "a",
        class_="container__link container__link--type-article container_vertical-strip__link",
    )
    for link in articles:
        full_link = urljoin(base_url, link["href"])
        links.append(full_link)
    return links


with open("channel_automation/services/crawler/sources/cnn_news.html") as f:
    html = f.read()
links = extract_news_links(html)
print(links)
