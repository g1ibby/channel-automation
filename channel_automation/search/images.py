from typing import List

import re

import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

from channel_automation.interfaces.search_interface import IImageSearch


class BingImageSearch:
    def __init__(self):
        pass

    def search_images(self, query: str, num_images: int = 5) -> list[str]:
        url = f"https://www.bing.com/images/search?q={query.replace(' ', '+')}&qft=+filterui%3Aimagesize-large"
        soup = BeautifulSoup(requests.get(url).text, "html.parser")

        image_urls = []
        for a in soup.find_all("a", {"class": "iusc"}):
            m = re.search('"murl":"(.*?)"', a.get("m"))
            if m:
                image_url = m.group(1)
                image_urls.append(image_url)
                if len(image_urls) >= num_images:
                    break

        return image_urls


# Define the GoogleImageSearch class, which implements the IImageSearch interface
class GoogleImageSearch(IImageSearch):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search_images(self, query: str, num_images: int = 5) -> list[str]:
        params = {
            "q": query,
            "tbm": "isch",  # Image search
            "api_key": self.api_key,
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        image_urls = []
        if "images_results" in results:
            for image_result in results["images_results"]:
                if "original" in image_result:
                    image_urls.append(image_result["original"])

                # Stop collecting image URLs when the desired number of images is reached
                if len(image_urls) >= num_images:
                    break

        return image_urls
