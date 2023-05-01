from typing import List

from abc import ABC, abstractmethod


# Define the IImageSearch interface, which is an abstract class
class IImageSearch(ABC):
    # Declare an abstract method called search_images
    # This method should take a query string and the number of images to return, and return a list of image URLs
    @abstractmethod
    def search_images(self, query: str, num_images: int) -> list[str]:
        pass
