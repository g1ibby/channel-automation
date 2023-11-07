import pytest

from channel_automation.services.crawler.sources.tatnews import (
    TatnewsCrawler,  # Adjust import path as necessary
)


@pytest.mark.asyncio
async def test_tatnews_crawler():
    async with TatnewsCrawler() as crawler:
        articles = await crawler.crawl()
        assert len(articles) > 1  # Ensure more than one news article is returned

        for article in articles:
            assert article.title  # Check that title exists
            assert article.text  # Check that text exists
