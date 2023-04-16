from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch

from channel_automation.interfaces.es_repository_interface import INewsArticleRepository
from channel_automation.models import NewsArticle


class ElasticsearchNewsArticleRepository(INewsArticleRepository):
    def __init__(self, host: str, port: int):
        self.es = self.init_elasticsearch(host, port)
        self.index = "news"

    def init_elasticsearch(self, host: str, port: int) -> Elasticsearch:
        try:
            es = Elasticsearch(
                [{"host": host, "port": port, "scheme": "http"}],
                basic_auth=("elastic", "elastic"),
            )
            if es.ping():
                print("Elasticsearch connected.")
                return es
            else:
                print("Elasticsearch connection failed.")
                return None
        except Exception as e:
            print(f"Error connecting to Elasticsearch: {e}")
            return None

    def save_news_article(self, news_article: NewsArticle) -> NewsArticle:
        doc_id = news_article.id
        document = news_article.__dict__
        self.index_document(doc_id, document)
        return news_article

    def index_document(
        self, doc_id: str, document: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        try:
            response = self.es.index(index=self.index, id=doc_id, document=document)
            return response
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

        articles = [
            NewsArticle(**hit["_source"]) for hit in search_results["hits"]["hits"]
        ]

        return articles
