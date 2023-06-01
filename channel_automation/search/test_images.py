import unittest

from channel_automation.interfaces.search_interface import IImageSearch
from channel_automation.search.images import BingImageSearch


class BingImageSearchTest(unittest.TestCase):
    def setUp(self):
        self.image_search = BingImageSearch()

    def test_search_images(self):
        query = "cats"
        num_images = 5
        results = self.image_search.search_images(query, num_images)

        # Check that we got the correct number of image URLs
        self.assertEqual(len(results), num_images)

        # Check that all URLs are strings and non-empty
        for url in results:
            self.assertIsInstance(url, str)
            self.assertTrue(len(url) > 0)


if __name__ == "__main__":
    unittest.main()
