import pytest

from channel_automation.services.crawler.sources.thephuketnews import PhuketNewsCrawler


@pytest.mark.asyncio
async def test_phuketnews_crawler():
    async with PhuketNewsCrawler() as crawler:
        articles = await crawler.crawl()
        assert len(articles) > 1  # Ensure more than one news article is returned

        for article in articles:
            assert article.title  # Check that title exists
            assert article.text  # Check that text exists


@pytest.mark.asyncio
async def test_extract_content():
    async with PhuketNewsCrawler() as crawler:
        url = "https://www.thephuketnews.com/polking-lavishes-praise-on-his-men-after-estonia-draw-89960.php"
        article = await crawler.extract_content(url)
        print(article)

        assert article is not None  # Check that an article is returned
        assert article.title  # Check that the title exists
        assert article.text  # Check that the text exists
        assert len(article.images_url) > 0  # Check that there is at least one image
