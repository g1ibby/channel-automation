import json

import requests


def get_tourismthailand_breaking_news_links():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Language": "en",
        "Origin": "https://www.tourismthailand.org",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": "https://www.tourismthailand.org/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    url = "https://api.tourismthailand.org/api/home/get_breaking_news?Language=en&timestamp=1696224885086"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        parsed_json = json.loads(response.text)
        news_links = [news["url"] for news in parsed_json["result"]]
        return news_links
    else:
        print(f"Failed to retrieve news. HTTP Status Code: {response.status_code}")
        return None


def get_tourismthailand_announcement_links():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Language": "en",
        "Origin": "https://www.tourismthailand.org",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": "https://www.tourismthailand.org/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    url = "https://api.tourismthailand.org/api/home/get_news_announcement?Language=en&timestamp=1696224885086"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        parsed_json = json.loads(response.text)
        announcement_links = [
            f"https://www.tourismthailand.org/Articles/{announcement['slug']}"
            for announcement in parsed_json["result"]
        ]
        return announcement_links
    else:
        print(
            f"Failed to retrieve announcements. HTTP Status Code: {response.status_code}"
        )
        return None


# To use this function in your crawler:
if __name__ == "__main__":
    news_links = get_tourismthailand_breaking_news_links()
    if news_links:
        for link in news_links:
            print(link)

    announcement_links = get_tourismthailand_announcement_links()
    if announcement_links:
        for link in announcement_links:
            print(link)
