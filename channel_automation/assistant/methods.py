import openai

from channel_automation.interfaces.assistant_interface import IAssistant
from channel_automation.models import NewsArticle

template = (
    "You are a helpful assistant that helps me to create social networks posts and work with news papers."
    "I will give you text of a newspaper "
    "and you should create social network post(about 200 words, can be much less) about this this paper."
    "The post should be in Russian language. This post should be formal but also interesting to read."
    "You can use emojis in posts."
    "Also, newspapers sometimes can contains two or more different parts of text which do not related to each "
    "other,"
    "please write social network post only about first part and ignore others."
    "The post should be in Russian language. That's very important!"
)


class Assistant(IAssistant):
    def __init__(self, api_token: str):
        openai.api_key = api_token
        pass

    def process_and_translate_article(self, news_article: NewsArticle) -> NewsArticle:
        result = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": template},
                {"role": "user", "content": news_article.text},
            ],
        )
        answer = result["choices"][0]["message"]["content"]
        news_article.russian_abstract = answer
        return news_article
