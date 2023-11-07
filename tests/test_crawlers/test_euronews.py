import pytest

from channel_automation.services.crawler.sources.euronews import EuronewsTourismCrawler


@pytest.mark.asyncio
async def test_euronews_crawler():
    async with EuronewsTourismCrawler(
        "https://www.euronews.com/tag/tourism"
    ) as crawler:
        articles = await crawler.crawl()
        assert len(articles) > 1  # Ensure more than one news article is returned

        for article in articles:
            assert article.title  # Check that title exists
            assert article.text  # Check that text exists


@pytest.mark.asyncio
async def test_extract_content():
    async with EuronewsTourismCrawler(
        "https://www.euronews.com/tag/tourism"
    ) as crawler:
        url = "https://www.euronews.com/travel/2023/10/25/a-big-culture-pot-singer-songwriter-foy-vance-plays-and-eats-his-way-through-baton-rouge"
        article = await crawler.extract_content(url)

        assert article is not None  # Check that an article is returned
        assert article.title  # Check that the title exists
        assert article.text  # Check that the text exists
        assert len(article.images_url) > 0  # Check that there is at least one image

        url = "https://www.euronews.com/travel/2023/10/25/want-to-move-to-spain-you-could-buy-yourself-this-village-for-the-same-price-as-a-house"
        article = await crawler.extract_content(url)

        assert article is not None  # Check that an article is returned
        assert article.title  # Check that the title exists
        assert article.text  # Check that the text exists
        assert len(article.images_url) > 0  # Check that there is at least one image
