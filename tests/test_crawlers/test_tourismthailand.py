import pytest

from channel_automation.services.crawler.sources.tourismthailand import (
    TourismthailandCrawler,
)


@pytest.mark.asyncio
async def test_tatnews_crawler():
    crawler = TourismthailandCrawler()
    articles = await crawler.crawl()
    assert len(articles) > 1  # Ensure more than one news article is returned

    for article in articles:
        assert article.title  # Check that title exists
        assert article.text  # Check that text exists
