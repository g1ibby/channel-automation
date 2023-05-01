import json
import re

import openai

from channel_automation.assistant.models import PostData
from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.models import NewsArticle

template = """
You are a helpful assistant that helps me to create social network posts based on newspapers.
I will give you the text from a newspaper and you should do two tasks:
1. Create a social network post(about 150 words, which can be much less) about this newspaper. The post should be in the Russian language. This post should be formal but also interesting to read. You can use emojis in posts. Also, newspapers sometimes can contain two or more different parts of the text which do not relate to each other, please write social network posts only about the first part and ignore others. The post should be in the Russian language. That's very important!
Don't need to put any hashtags to the post.
The post also should be in Markdown format for Telegram Messenger.
2. Create a Google search request to find suitable images for this social network post in English.

You should return the result in JSON format with the fields: social_post, images_search
"""

bottom_template = """Будь в курсе последних новостей:
[Мой Таиланд 🇹🇭](https://t.me/THE_THAILAND/485)
[Night Life Thailand 🇹🇭](https://t.me/NIGHT_LIFE_THAILAND)
[Sport Thailand 🇹🇭](https://t.me/thailand_sport)
[Тайская аптечка 🚑](https://t.me/thai_med/62)"""


def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [
        {"role": "system", "content": template},
        {"role": "user", "content": prompt},
    ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0,  # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]


def parse_json_to_dataclass(json_text: str) -> PostData:
    json_data = json.loads(json_text)
    return PostData(**json_data)


class Assistant(IAssistant):
    def __init__(self, api_token: str):
        openai.api_key = api_token
        pass

    def process_and_translate_article(self, news_article: NewsArticle) -> NewsArticle:
        result_json = get_completion(news_article.text, "gpt-4")
        post_data = parse_json_to_dataclass(result_json)
        news_article.russian_abstract = post_data.social_post
        news_article.images_search = post_data.images_search
        return news_article
