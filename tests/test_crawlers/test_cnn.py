import pytest

from channel_automation.services.crawler.sources.cnn import CNNTravelNewsCrawler


@pytest.mark.asyncio
async def test_cnn_crawler():
    crawler = CNNTravelNewsCrawler()
    articles = await crawler.crawl()
    assert len(articles) > 1  # Ensure more than one news article is returned

    for article in articles:
        assert article.title  # Check that title exists
        assert article.text  # Check that text exists


@pytest.mark.asyncio
async def test_extract_content():
    crawler = CNNTravelNewsCrawler()
    url = "https://edition.cnn.com/travel/blue-ridge-parkway-section-closed-feeding-bear/index.html"
    article = await crawler.extract_content(url)

    assert article is not None  # Check that an article is returned
    assert article.title  # Check that the title exists
    assert article.text  # Check that the text exists
    assert len(article.images_url) > 0  # Check that there is at least one image

    url = "https://edition.cnn.com/travel/world-beating-cities-for-food-and-drink/index.html"
    article = await crawler.extract_content(url)

    assert article is not None  # Check that an article is returned
    assert article.title  # Check that the title exists
    assert article.text  # Check that the text exists
    assert len(article.images_url) > 0  # Check that there is at least one image
