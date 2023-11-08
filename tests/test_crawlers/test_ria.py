import pytest

from channel_automation.services.crawler.sources.ria import RiaNewsCrawler


@pytest.mark.asyncio
async def test_ria_crawler():
    async with RiaNewsCrawler() as crawler:
        articles = await crawler.crawl()
        assert len(articles) > 1  # Ensure more than one news article is returned

        for article in articles:
            assert article.title  # Check that title exists
            assert article.text  # Check that text exists


@pytest.mark.asyncio
async def test_extract_content():
    async with RiaNewsCrawler() as crawler:
        url = "https://ria.ru/20231108/puteshestviya-1907985347.html"
        article = await crawler.extract_content(url)

        assert article is not None  # Check that an article is returned
        assert article.title  # Check that the title exists
        assert article.text  # Check that the text exists
