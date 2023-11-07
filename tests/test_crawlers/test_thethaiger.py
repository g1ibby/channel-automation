import pytest

from channel_automation.services.crawler.sources.thethaiger import ThethaigerNewsCrawler


@pytest.mark.asyncio
async def test_thethaiger_crawler():
    async with ThethaigerNewsCrawler() as crawler:
        articles = await crawler.crawl()
        assert len(articles) > 1  # Ensure more than one news article is returned

        for article in articles:
            assert (
                "/live-news/" not in article.source
            )  # Check that the link is not a live news link
            assert article.title  # Check that title exists
            assert article.text  # Check that text exists


@pytest.mark.asyncio
async def test_extract_content():
    async with ThethaigerNewsCrawler() as crawler:
        url = "https://thethaiger.com/news/national/thai-woman-calls-justice-after-thai-man-attacks-her-belgian-husband"
        article = await crawler.extract_content(url)

        assert article is not None  # Check that an article is returned
        assert article.title  # Check that the title exists
        assert article.text  # Check that the text exists
