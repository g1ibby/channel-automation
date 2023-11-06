import pytest

from channel_automation.services.crawler.sources.clubbingthailand import (
    ClubbingThailandCrawler,
)


@pytest.mark.asyncio
async def test_clubbingthailand_crawler():
    crawler = ClubbingThailandCrawler()
    articles = await crawler.crawl()
    assert len(articles) > 1  # Ensure more than one news article is returned

    for article in articles:
        assert article.title  # Check that title exists
        assert article.text  # Check that text exists


@pytest.mark.asyncio
async def test_extract_content():
    crawler = ClubbingThailandCrawler()
    url = "https://clubbingthailand.com/sugar-club-bangkok-presents-mask-on-masquerade-8th-anniversary/"
    article = await crawler.extract_content(url)

    assert article is not None  # Check that an article is returned
    assert article.title  # Check that the title exists
    assert article.text  # Check that the text exists
    assert len(article.images_url) > 0  # Check that there is at least one image
