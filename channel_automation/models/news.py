from typing import List, Optional

from dataclasses import dataclass, field


@dataclass
class Post:
    social_post: str
    images_search: Optional[str] = None
    images_id: list[str] = field(default_factory=list)
    images_url: list[str] = field(default_factory=list)


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
    posts: list[Post] = field(default_factory=list)
    # we don't need this field. Keep it here because we have these fields in database
    russian_abstract: Optional[str] = field(default=None)
    images_search: Optional[str] = field(default=None)
    images_url: list[str] = field(default_factory=list)
