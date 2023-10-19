import json

import openai

from channel_automation.assistant.models import PostData
from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.models import NewsArticle

template1 = """
You are an assistant responsible for creating social media posts based on newspaper articles. Here are your two tasks:

1. Generate a social media post of approximately 150 words based on the newspaper text I provide. The post must be written in Russian. Aim for a formal yet engaging tone. You may include emojis for emphasis. If the newspaper text contains multiple unrelated sections, focus only on the first section for the social media post. Please note that the post must be in Markdown format suitable for Telegram Messenger. There's no need to include any hashtags or links.

2. Create an English-language Google search query to find appropriate images to accompany the social media post.

Additional Guidelines:

- If the social media post exceeds a certain length, consider breaking it into paragraphs to improve readability. A well-structured post with multiple paragraphs makes it easier for the audience to engage with and understand the content.

- There's no need to include website links or URLs at the end of the post unless specifically instructed to do so. Excluding them helps maintain a clean and focused presentation of the content.

Your answer will always be a single social post, and must always be in valid JSON format.

EXAMPLES:

OUTPUT:
{"social_post": "*Current Situation in Thailand* Таиланд в настоящее время сталкивается с тем, что, по прогнозам многих экспертов, перерастет в серьезную вспышку лихорадки денге, с вероятностью до 150 000 случаев заражения к концу года.", "images_search": "dengue"}

OUTPUT:
{"social_post": "*Visa Policy Update* ⏺ Новое правительство Таиланда планирует увеличить срок безвизового пребывания российских туристов в стране с 30 до 90 дней.", "images_search": "thailand visa tourists"}
"""

template2 = """
You are an assistant responsible for creating social media posts based on newspaper articles. Here are your tasks:

1. Generate a social media post of approximately 150 words based on the newspaper text I provide.
  - **Title**: Each post should start with a title, enclosed in asterisks for bold text in Markdown format (e.g., `*Title Here*`). Follow the title with two empty lines.
  - **Language**: The post must be written in Russian.
  - **Tone**: Aim for a formal yet engaging tone. You may include emojis for emphasis.
  - **Content**: If the newspaper text contains multiple unrelated sections, focus only on the first section for the social media post.
  - **Paragraphs**: For longer posts, break the text into paragraphs to enhance readability.
  - **Links**: Do not include website links or URLs at the end of the post unless specifically instructed to do so.
  - **Format**: The post should be in Markdown format suitable for Telegram Messenger.

2. Create an English-language Google search query to find appropriate images to accompany the social media post.

Your answer will always be a single social post, and must always be in valid JSON format.

EXAMPLES:

OUTPUT:
{"social_post": "*Current Situation in Thailand* Таиланд в настоящее время сталкивается с тем, что, по прогнозам многих экспертов, перерастет в серьезную вспышку лихорадки денге, с вероятностью до 150 000 случаев заражения к концу года.", "images_search": "dengue"}

OUTPUT:
{"social_post": "*Visa Policy Update* ⏺ Новое правительство Таиланда планирует увеличить срок безвизового пребывания российских туристов в стране с 30 до 90 дней.", "images_search": "thailand visa tourists"}
"""

templates = {
    1: template1,
    2: template2,
}


def get_completion(prompt, template):
    messages = [
        {"role": "system", "content": template},
        {"role": "user", "content": prompt},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.51,
        max_tokens=2261,
        top_p=0,
        frequency_penalty=0,
        presence_penalty=0,
    )
    if "choices" not in response or not response.choices:
        raise ValueError("No choices in response.")

    first_choice = response.choices[0]
    if "message" not in first_choice or "content" not in first_choice.message:
        raise ValueError("Missing 'message' or 'content' in the first choice.")

    return first_choice.message["content"]


def parse_json_to_dataclass(json_text: str) -> PostData:
    # Escape newlines and tabs
    escaped_json_text = json_text.replace("\n", "\\n").replace("\t", "\\t")
    try:
        json_data = json.loads(escaped_json_text)
        return PostData(**json_data)
    except json.JSONDecodeError as e:
        print(f"JSON text: {escaped_json_text}")
        raise ValueError(f"Invalid JSON format: {e}")


class Assistant(IAssistant):
    def __init__(self, api_token: str):
        openai.api_key = api_token
        pass

    def process_and_translate_article(
        self, news_article: NewsArticle, variation_number: int
    ) -> NewsArticle:
        try:
            chosen_template = templates.get(variation_number, template1)
            result_json = get_completion(news_article.text, chosen_template)
            post_data = parse_json_to_dataclass(result_json)

            news_article.russian_abstract = post_data.social_post
            news_article.images_search = post_data.images_search
            return news_article
        except Exception as e:
            # Optional: log the exception
            raise  # This will propagate the exception up a level
