import pytest

from channel_automation.services.crawler.sources.thepattayanews import (
    ThepattayaNewsCrawler,
)


@pytest.mark.asyncio
async def test_thepattayanews_crawler():
    async with ThepattayaNewsCrawler() as crawler:
        articles = await crawler.crawl()
        assert len(articles) > 1  # Ensure more than one news article is returned

        for article in articles:
            assert article.title  # Check that title exists
            assert article.text  # Check that text exists


@pytest.mark.asyncio
async def test_extract_content():
    async with ThepattayaNewsCrawler() as crawler:
        url = "https://thepattayanews.com/2023/10/02/so-called-activist-k-100-million-creates-chaos-on-pattayas-sukhumvit-road/"
        article = await crawler.extract_content(url)
        print(article)

        assert article is not None  # Check that an article is returned
        assert article.title  # Check that the title exists
        assert article.text  # Check that the text exists
