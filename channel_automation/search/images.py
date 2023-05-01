from typing import List

from serpapi import GoogleSearch

from channel_automation.interfaces.search_interface import IImageSearch


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
