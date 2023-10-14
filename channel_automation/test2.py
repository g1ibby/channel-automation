import asyncio

from channel_automation.services.crawler.sources.bangkokpost import BangkokpostCrawler

# To run the crawler
if __name__ == "__main__":

    async def main():
        crawler = BangkokpostCrawler()
        articles = await crawler.crawl()
        print(articles)

    asyncio.run(main())
