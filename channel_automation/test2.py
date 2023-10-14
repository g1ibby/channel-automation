import asyncio

from channel_automation.services.crawler.sources.tourismthailand import (
    TourismthailandCrawler,
)

# To run the crawler
if __name__ == "__main__":

    async def main():
        crawler = TourismthailandCrawler()
        articles = await crawler.crawl()
        print(articles)

    asyncio.run(main())
