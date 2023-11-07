import pytest

from channel_automation.services.crawler.sources.bangkokpost import BangkokpostCrawler


@pytest.mark.asyncio
async def test_bangkokpost_crawler():
    async with BangkokpostCrawler() as crawler:  # Use the crawler as an async context manager
        articles = await crawler.crawl()
        assert len(articles) > 1  # Ensure more than one news article is returned

        for article in articles:
            assert article.title  # Check that title exists
            assert article.text  # Check that text exists
