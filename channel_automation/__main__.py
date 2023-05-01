# type: ignore[attr-defined]
from typing import List, Optional

import asyncio
from enum import Enum
from random import choice

import typer
from revChatGPT.V1 import Chatbot
from rich.console import Console
from sqlmodel import Session, SQLModel, create_engine

from channel_automation import version
from channel_automation.assistant.methods import Assistant
from channel_automation.bot import run_bot
from channel_automation.data_access.elasticsearch.methods import ESRepository
from channel_automation.data_access.postgresql.methods import Repository
from channel_automation.example import hello
from channel_automation.models import ChannelInfo
from channel_automation.models.source import Source
from channel_automation.search.images import GoogleImageSearch
from channel_automation.services.bot import TelegramBotService
from channel_automation.services.news_crawler import NewsCrawlerService


class Color(str, Enum):
    white = "white"
    red = "red"
    cyan = "cyan"
    magenta = "magenta"
    yellow = "yellow"
    green = "green"


app = typer.Typer(
    name="channel-automation",
    help="channel-automation is tool to atomate telegram channels",
    add_completion=False,
)
console = Console()


def version_callback(print_version: bool) -> None:
    """Print the version of the package."""
    if print_version:
        console.print(f"[yellow]channel-automation[/] version: [bold blue]{version}[/]")
        raise typer.Exit()


@app.command(name="")
def main(
    name: str = typer.Option(..., help="Person to greet."),
    color: Optional[Color] = typer.Option(
        None,
        "-c",
        "--color",
        "--colour",
        case_sensitive=False,
        help="Color for print. If not specified then choice will be random.",
    ),
    print_version: bool = typer.Option(
        None,
        "-v",
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Prints the version of the channel-automation package.",
    ),
) -> None:
    """Print a greeting with a giving name."""
    if color is None:
        color = choice(list(Color))

    greeting: str = hello(name)
    console.print(f"[bold {color}]{greeting}[/]")


@app.command(name="bot")
def bot(token: str = typer.Option(..., help="Telegram bot token.")) -> None:
    """Run the bot."""
    run_bot(token)


@app.command(name="bot2")
def bot2() -> None:
    """Run the bot."""
    SERP_API_KEY = "ed694bfc6af60767a2f7cb3345477c22effca088fb2a795450e86b2f16abc354"
    TELEGRAM_BOT_TOKEN = "2039441709:AAFlyagf7AIMtZ0WuHJ0FjLwxn85-4r5HP0"
    ADMIN_CHAT_ID = "1672563160"
    DATABASE_URL = "postgresql://user:password@localhost/automation"

    repository = Repository(DATABASE_URL)
    es_repo = ESRepository(host="localhost", port=9200)
    assistant = Assistant("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")
    image_search = GoogleImageSearch(api_key=SERP_API_KEY)
    telegram_bot_service = TelegramBotService(
        TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID, repository, es_repo, assistant, image_search
    )

    telegram_bot_service.run()


@app.command(name="crawler")
def crawler() -> None:
    """Run the crawler."""
    print("crawler")
    # Initialize the ElasticsearchNewsArticleRepository with the host and port
    repository = ESRepository(host="localhost", port=9200)

    # Initialize the NewsCrawlerService with the news_article_repository instance
    news_crawler_service = NewsCrawlerService(news_article_repository=repository)

    # Crawl and extract news articles starting from the main page
    main_page = "https://www.bangkokpost.com/travel"
    extracted_articles = news_crawler_service.crawl_and_extract_news_articles(main_page)

    for article in extracted_articles:
        print(f"Title: {article.title}\nDate: {article.date}\n")

    # Schedule the news crawling to run every 30 minutes
    news_crawler_service.schedule_news_crawling(interval_minutes=30)

    # To keep the main thread alive, you can use an infinite loop or use an event to wait
    import time

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping the scheduler...")


@app.command(name="test-db-2")
def test_db_two() -> None:
    """Run the test-db."""
    print("test-db")
    DATABASE_URL = "postgresql://user:password@localhost/automation"
    repo = Repository(DATABASE_URL)

    # Add or update a channel
    channel_to_add = ChannelInfo(id="-100123456789", title="Sample Channel")
    added_channel = repo.add_channel(channel_to_add)
    print(f"Added channel: {added_channel}")

    channel_to_add = ChannelInfo(id="-100123456799", title="Sample Channel 2")
    added_channel = repo.add_channel(channel_to_add)
    print(f"Added channel: {added_channel}")

    # Remove a channel by its ID
    channel_id_to_remove = "-100123456789"
    repo.remove_channel(channel_id_to_remove)
    print(f"Removed channel with ID: {channel_id_to_remove}")

    # Get all channels
    all_channels = repo.get_all_channels()
    print("All channels:")
    for channel in all_channels:
        print(channel)


@app.command(name="test-db")
def test_db() -> None:
    """Run the test-db."""
    print("test-db")
    DATABASE_URL = "postgresql://user:password@localhost/automation"
    repository = Repository(DATABASE_URL)
    # Add a new sources
    new_source = Source(link="https://example.com")
    repository.add_source(new_source)
    new_source2 = Source(link="https://example2.com")
    repository.add_source(new_source2)

    # Disable a source
    repository.disable_source(new_source.id)

    # Get all active sources
    active_sources = repository.get_active_sources()
    for source in active_sources:
        print(source.link)


@app.command(name="gpt")
def gpt() -> None:
    """Run the gpt."""
    chatbot = Chatbot(
        config={
            "session_token": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..JPGxZjRtgBRJYPnD.wzIEirGJ94hVRxSbcmy38wt-YLNTdsZDaw9ztG159mfzBIm9jwSVwMJQKUpxCii76doDDy-dbJ99QkhdfALhAXM7L9aHjvyG7nLwCNysChyv7dMvxZYXfkW-srg0-jCD3KAtJPsJb0pNC1EUi2iMVca2T76mOvz9Bw3wYhMWK1IlFmwFamZ8-WzGmFBmFyDwaw2Em6WgRlgFyYUC_0HAUvXl8CVjZakQZqn-ptg5Egi9zwd5Tohd8lKOR5ylBRziM0KBhKkqV7juLEG9oD_jfM5JcgQpb8-SoBlVqCkyu9bF2ZIHqMpaXj8WRv70-kYw0nf6dglvH2WdgzXS275pVkiJr1xAfIZzDmyzHkN5DJFRI6IHZptnzsusWP1DTSG_GUMdmaqIit5wpDHWhcCiW0oUwz1oGIFw4gnxzCJGEnWBjx5VdPlbQ_KKAGRfdMVfyVYDHZeoKWF0HdIuqYu8b-6-zEjPauN9s5NSyvjfZOF_qZNZsvx_z3_ki2CA7_S6MaW1quPi-wWN_t_eS2PXKXoF7Qi54sipCirecmCM1w_MNVdQzRDyNxz92uhIgrSQHx21ggcTFpY5ybx_kHHscEnzSRKb8BBIwFeVpq-2WMwSrI-x4J5QPinfTr6gw9s7F9MqMiT3YqiR9g1bPycDTwnKiy9bxFSTwpm3QnTHpnoZOVZz0kb9nW7oZ0YyRabwjmmdBvjUb-cR4ceyAlpR9WWQ8GFxMlry9sJuzabNPgClwi28iiXncRuJhVdYvsSPJADhg8UgxdevybUvVjpwXOj2iFuRUX5MnNz-DyX-NFTgVai9AFaHO7O89cl41Qs3J1lTg48wQe0sry3nreqFMjBlH_cUdJbISsgAyGuTzvNdsiz5YA3M_u9dZaZRdaxdKE8ySt63Do27ALKFhU2T12HmWLJhC-7gcnRSXi6HZTlQwF5vlWYuVUCXW6s0v3RSVOyejZ2XLlo2VWQ91rrKkhjwKfen1CXm3DlYIvSG1fdxAXtns2xYCl16cKf_9SFmxSA6ELH_m5-IBUH6r3tOOXBdjvTXEi25eYXQn5j8fkWqtwW7HGv1ZC_YSMDERfB6Y3-Tj2xzCmpR2HK4W0qfvafFTU-RhZAH82dsl-77z3aO6DM0x5zXdNednzOjelwzSPzWoKZ-corTR5qwZZ1M6Ae6K--Y57OMcCNSH9CB7Ut2l6toXoWI2EDKcf_au9oSCaWWPc9F_ve96_zZVhljXvER0pkwi__QiqGJC3pyd09ZTnvxAq19mWoA0G9i0UsE_02tk3tFLSfAac9sNrxi2W2QYeFCWTNwBQQ4hcituiNSwKY6_htv5nxJPXuyWu_zGTV4hcwdrLugvQvi0dybkMq3nYW53RZ-IHpmy_Y8Odj_p0GOW2DRkvbiZYHdgYtyho1T_LImiA__vBpKsJnZEu1wfrmir_Bpe30jMu661eHeXituqgt8P9TCLOUJoKMxU_FgKcZkC47sQnlLJyOS271pddiDgQJDc5pcXjhfBlVe7Kkp67PbAUSpEUGg18E6kR5hEezZY6msW-bsDYjbIp6KNF4wgj--Yq1bHNC3UKL-UDSHUwXBejaYEg73zcOCu955BiJvz1vbzF04R0BeBfe-4vjf0__44Mx2-1kFCwGUpQiB-zcIo4KC6P0KaSmOVasQis3tzF_8kvmIEVfCGRmT8UiuRD9IB4Hzk7gPUgStGv2Z7y5gUPkAXoL3rIK1XHJFt1Oga9l_7JCr82mWEvoqEeJqW24Yu-Z_qSqK58Mwup1UcOUO6jjK6gcjxy3IcxHwbalD6OUN4C9x_QXKhYXl_l07QOwLTRWchrIZRQXN9_6liABCEfRSGNvEUtkc1cqYm9KpMYckQDLtpE788hIFXyeX3gAmtUX7l0vFIHuy1x2bseY4ctK981lw-nP2qZ1m_q61PFSIDcUlxGRe5PGxKxO6ZwZA7jbaGJ8g_Yg3RjYztWG4vRUU4xMcKJyXEDn9wki_wcRY697QApT7Pw6V8enpy2vp0dcG1gjDceqH9VXt-AX_zpCIkNy31ipATo1f2Bbw1WA-ZL4PL3KrEZrJ3V8noMUQvXeGLj8Lkpoot4wxJeREhz-tjFKs4bSiJNsEgzNO1Uf-bhfAFAECb-JGaCHayjOey2eFaJgPlym0SlAGA9xIZIAEGUL8NDZKpvZ-Uv_ug2kYD01dSi3wBIR3N_411mTBPwXXdN9IQzL76KXCfIVjMC0a9idFnBbZ7s9i_O3bRmB5usaXf1TJ9UU7b7vKiKqyFa-vWWqgdySsvFCZLLpqqXlmMuiVcDqh9KDvcATZ61JpS3_2NMftE9iYJ5KxczAA84kDiTVO16x2EvNOmzPoOPAtWnQv2I_vH0B7Y3CLCROdnnZpj_k2BTA9Coei5a17-m5sCWiO9UUHTZ5B1UbH9DFPBCq69v3fWFfmlzKCNR5OLNTy4_fzGAUAo3SPhFFYIXhyg4EFUEWbmrHOwDQYz87RWxKuXoGzLpPx1xxoNKfRhlmK0ScaxXqTGwidmkUazXjoWjjvCb19qZCw5KYaTmYELjmT6wCPSchULFadkTd-FrUjZpk4iHpCdX8e3HArIyhThQLZLlXAwtwCAJORsV1aMJMsrRI8TdMDhQ1T3hOpXQCDLQmc_Lb-A4LT16eT_yYK9V_Elwko3umWWXtjMw.QxzglLL7tGwTTssVZUHE0w",
        }
    )
    prompt = "how many beaches does portugal have?"
    response = ""
    for data in chatbot.ask(prompt):
        response = data["message"]

    print(response)


@app.command(name="gpt2")
def gpt2() -> None:
    print("gpt2")
    assist = Assistant("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")
    repository = ESRepository(host="localhost", port=9200)
    news = repository.get_latest_news(1)
    print(news[0].text)
    res_news = assist.process_and_translate_article(news[0])
    print(res_news.russian_abstract)
    repository.update_news_article(res_news)


@app.command(name="img")
def img() -> None:
    API_KEY = "ed694bfc6af60767a2f7cb3345477c22effca088fb2a795450e86b2f16abc354"
    image_search = GoogleImageSearch(api_key=API_KEY)
    # Define a search query and the number of images you want to retrieve
    search_query = "beautiful landscape"
    num_images = 5

    # Use the search_images method to search for images
    image_urls = image_search.search_images(query=search_query, num_images=num_images)

    # Print the retrieved image URLs
    for i, url in enumerate(image_urls):
        print(f"Image {i + 1}: {url}")


if __name__ == "__main__":
    app()
