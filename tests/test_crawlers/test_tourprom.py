import pytest

from channel_automation.services.crawler.sources.tourprom import TourpromNewsCrawler


@pytest.mark.asyncio
async def test_tourprom_crawler():
    async with TourpromNewsCrawler("https://www.tourprom.ru/news/") as crawler:
        articles = await crawler.crawl()
        assert len(articles) > 1  # Ensure more than one news article is returned

        for article in articles:
            assert article.title  # Check that title exists
            assert article.text  # Check that text exists


@pytest.mark.asyncio
async def test_extract_content():
    async with TourpromNewsCrawler("https://www.tourprom.ru/news/") as crawler:
        url = "https://www.tourprom.ru/news/62497/"
        article = await crawler.extract_content(url)

        assert article is not None  # Check that an article is returned
        assert article.title  # Check that the title exists
        assert article.text  # Check that the text exists
