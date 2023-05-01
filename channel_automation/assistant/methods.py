import re

import openai

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.models import NewsArticle

template = (
    "You are a helpful assistant that helps me to create social networks posts and work with news papers."
    "I will give you text of a newspaper "
    "and you should create social network post(about 150 words, can be much less) about this this paper."
    "The post should be in Russian language. This post should be formal but also interesting to read."
    "You can use emojis in posts."
    "Also, newspapers sometimes can contains two or more different parts of text which do not related to each "
    "other,"
    "please write social network post only about first part and ignore others."
    "The post should be in Russian language. That's very important!"
    "The post also should be in Markdown format for Telegram messanger."
)

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


class Assistant(IAssistant):
    def __init__(self, api_token: str):
        openai.api_key = api_token
        pass

    def process_and_translate_article(self, news_article: NewsArticle) -> NewsArticle:
        abstract = get_completion(news_article.text, "gpt-4")
        news_article.russian_abstract = abstract
        return news_article
