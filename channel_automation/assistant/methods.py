import json

import openai

from channel_automation.assistant.models import PostData
from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.models import NewsArticle, Post

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
  - **Title**: Each post should start with a title, enclosed in asterisks for bold text in Telegram Markdown format (e.g., `*Title Here*`). Follow the title with two empty lines.
  - **Language**: The post must be written in Russian.
  - **Tone**: Aim for a formal yet engaging tone. You may include emojis for emphasis.
  - **Content**: If the newspaper text contains multiple unrelated sections, focus only on the first section for the social media post.
  - **Paragraphs**: For longer posts, break the text into paragraphs to enhance readability.
  - **Links**: Do not include website links or URLs at the end of the post unless specifically instructed to do so.
  - **Format**: The post should be in Telegram Markdown format suitable for Telegram Messenger.

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

template_fancier = """
You are an assistant tasked with enhancing social media posts to make them more engaging, well-structured, and visually appealing. You will receive the initial social post in Telegram Markdown format as input.

- **Title**: Each post should begin with a title to capture the reader's attention. The title should be made bold by enclosing it in asterisks, like so: `*Title Here*`.
- **Readability**: Consider breaking the text into paragraphs for easier reading.
- **Emphasis**: Use Telegram Markdown formatting to make certain words bold or italic for emphasis.
- **Language**: The social post must be written exclusively in Russian.
- **Formatting**: Utilize Telegram Markdown formatting conventions for the entire social post.
- **Simplicity**: Return only the social post itself, without any additional comments or explanations.

Your ultimate goal is to generate a social post that is both compelling and well-organized.
"""

template_guidence = """
You are an assistant tasked with transforming social media posts according to user-provided guidelines. You will receive the initial social post and specific stylistic guidance from the user, both in Telegram Markdown format as input.

- **Title**: Each post should start with a title that aligns with the user's stylistic guidance. Make the title bold by enclosing it in asterisks, like so: `*Title Here*`.
- **Readability**: Break the text into paragraphs if suggested by the user for easier reading.
- **Emphasis**: Use Telegram Markdown formatting to make certain words bold or italic, based on the user's preferences.
- **Language**: The social post must be written exclusively in Russian.
- **Formatting**: Stick to Telegram Markdown formatting conventions for the entire social post.
- **User Guidance**: Follow the stylistic and content-related guidelines provided by the user.
- **Simplicity**: Return only the re-crafted social post, devoid of any additional comments or explanations.

Your ultimate goal is to generate a social post that adheres to the user's guidelines while being compelling and well-organized.
"""


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
    # Remove the trailing '\\n' if it exists
    if escaped_json_text.endswith("\\n"):
        escaped_json_text = escaped_json_text[:-2]
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

    def generate_post(self, news_article: NewsArticle, variation_number: int) -> Post:
        try:
            chosen_template = templates.get(variation_number, template1)
            result_json = get_completion(news_article.text, chosen_template)
            post_data = parse_json_to_dataclass(result_json)

            return Post(
                social_post=post_data.social_post, images_search=post_data.images_search
            )
        except Exception as e:
            print(e)
            # Optional: log the exception
            raise  # This will propagate the exception up a level

    def make_post_fancy(self, post: Post) -> Post:
        prompt = f"Edit social post:\n{post.social_post}"

        result = get_completion(prompt, template_fancier)
        post.social_post = result

        return post

    def post_guidence(self, post: Post, guidence: str) -> Post:
        prompt = f"Guidence:\n{guidence}\n\nSocial post:\n{post.social_post}"

        result = get_completion(prompt, template_guidence)
        post.social_post = result

        return post
