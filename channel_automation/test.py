import re

import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "X-Requested-With": "XMLHttpRequest",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": "https://www.bangkokpost.com/life/travel",
    "Cookie": "is_pdpa=1; bkp_survey=1; is_gdpr=1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


def extract_news_links(html_content):
    # Initialize a BeautifulSoup object
    soup = BeautifulSoup(html_content, "html.parser")

    # Initialize an empty list to store the news links
    specific_news_links = []

    # Find and loop through each news item
    for news_item in soup.find_all("div", class_="news--list boxnews-horizon"):
        link_tag = news_item.find("figure").find("a", href=True)

        if link_tag is not None:
            link = link_tag["href"]
            specific_news_links.append(link)

    return specific_news_links


def extract_news_links_regex(html_content):
    regex = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>[^<]*<h3>')
    links = re.findall(regex, html_content)

    return links


response = requests.get(
    "https://www.bangkokpost.com/v3/list_content/life/travel?page=1", headers=headers
)

print(response.text)
# Call the function and store the result
# news_links = extract_news_links(response.text)
news_links = extract_news_links_regex(response.text)

# Display the news links
print("List of News Links:")
for link in news_links:
    print(link)
