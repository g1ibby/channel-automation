from typing import Optional

from dataclasses import dataclass, field


@dataclass
class NewsArticle:
    title: str
    author: str
    hostname: str
    date: str
    categories: str
    tags: str
    fingerprint: str
    id: Optional[str]
    license: Optional[str]
    comments: Optional[str]
    raw_text: str
    text: str
    language: Optional[str]
    source: str
    source_hostname: str = field(metadata={"json_key": "source-hostname"})
    excerpt: str
    russian_abstract: Optional[str] = None
    images_search: Optional[str] = None
