from typing import Any, Optional

import copy
import time

from elasticsearch import Elasticsearch

from channel_automation.interfaces.es_repository_interface import IESRepository
from channel_automation.models import NewsArticle, Post


class ESRepository(IESRepository):
    def __init__(self, host: str, port: int, retries: int = 100, delay: int = 6):
        self.index = "news"
        self.es = self.init_elasticsearch(host, port, retries, delay)

    def init_elasticsearch(
        self, host: str, port: int, retries: int, delay: int
    ) -> Optional[Elasticsearch]:
        for attempt in range(retries):
            try:
                es = Elasticsearch(
                    [{"host": host, "port": port, "scheme": "http"}],
                    basic_auth=("elastic", "elastic"),
                )
                if es.ping():
                    print("Elasticsearch connected.")

                    # Check if index exists
                    if not es.indices.exists(index=self.index):
                        # Create index
                        es.indices.create(index=self.index, ignore=400)
                        print(f"Index '{self.index}' created.")

                    return es
                else:
                    print("Elasticsearch connection failed.")
            except Exception as e:
                print(f"Attempt {attempt + 1} - Error connecting to Elasticsearch: {e}")
            # If this is not the last attempt, sleep for the specified delay before retrying
            if attempt < retries - 1:
                time.sleep(delay)
        return None

    def article_exists(self, source: str) -> bool:
        search_results = self.es.search(
            index=self.index,
            body={
                "query": {"bool": {"filter": {"term": {"source.keyword": source}}}},
                "size": 1,  # we only need to know if at least one article exists
            },
        )
        return (
            search_results["hits"]["total"]["value"] > 0
        )  # returns True if an article exists, False otherwise

    def save_news_article(self, news_article: NewsArticle) -> Optional[NewsArticle]:
        print(f"Saving article with source {news_article.source}")
        if self.article_exists(news_article.source):
            print(f"Article with source {news_article.source} already exists.")
            return None  # or update the existing article, or handle this situation in some other way
        else:
            document = news_article.__dict__
            doc_id = self.index_document(document)
            news_article.id = doc_id
            return news_article

    def index_document(self, document: dict[str, Any]) -> Optional[str]:
        try:
            response = self.es.index(index=self.index, document=document)
            return response["_id"]
        except Exception as e:
            print(f"Error indexing document: {e}")
            return None

    def get_latest_news(self, count: int) -> list[NewsArticle]:
        return self.get_latest_news_articles(size=count)

    def get_latest_news_articles(self, size: int = 10) -> list[NewsArticle]:
        search_results = self.es.search(
            index=self.index,
            size=size,
            query={"match_all": {}},
            sort=[{"date": {"order": "desc"}}],
        )

        articles = []
        for hit in search_results["hits"]["hits"]:
            source = hit["_source"]
            source["id"] = hit["_id"]
            article = NewsArticle(**source)
            articles.append(article)

        return articles

    def update_news_article(self, news_article: NewsArticle) -> NewsArticle:
        doc_id = news_article.id
        document = copy.deepcopy(news_article.__dict__)
        try:
            # Convert Post objects to dictionaries
            document["posts"] = [
                post.__dict__ if isinstance(post, Post) else post
                for post in document["posts"]
            ]
        except Exception as e:
            print(f"Error converting posts to dictionaries: {e}")
            raise e

        try:
            self.update_document(doc_id, document)
        except Exception as e:
            print(f"Error updating document: {e}")
            raise e
        return news_article

    def update_document(
        self, doc_id: str, document: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        try:
            response = self.es.update(
                index=self.index, id=doc_id, body={"doc": document}
            )
            return response
        except Exception as e:
            print(f"Error updating document: {e}")
            return None

    def get_news_article_by_id(self, article_id: str) -> Optional[NewsArticle]:
        try:
            response = self.es.get(index=self.index, id=article_id)
            if response["found"]:
                article_data = response["_source"]
                article_data["id"] = response["_id"]
                # Convert list of dictionaries to list of Post objects
                if "posts" in article_data:
                    article_data["posts"] = [
                        Post(**post_data) for post_data in article_data["posts"]
                    ]

                return NewsArticle(**article_data)
        except Exception as e:
            print(f"Error retrieving document by ID: {e}")

        return None
