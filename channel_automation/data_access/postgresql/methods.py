from typing import List

from contextlib import contextmanager

from sqlmodel import Session, create_engine

from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.models.source import Source


class Repository(IRepository):
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)

    @contextmanager
    def _get_session(self):
        session = Session(self.engine)
        try:
            yield session
        finally:
            session.close()

    def add_source(self, source: Source) -> Source:
        with self._get_session() as session:
            existing_source = (
                session.query(Source).filter(Source.link == source.link).one_or_none()
            )
            if existing_source:
                existing_source.is_active = True
                session.commit()
                return existing_source
            else:
                session.add(source)
                session.commit()
                session.refresh(source)
                return source

    def disable_source(self, source_id: int) -> None:
        with self._get_session() as session:
            source = session.get(Source, source_id)
            if source:
                source.is_active = False
                session.commit()

    def get_active_sources(self) -> list[Source]:
        with self._get_session() as session:
            return session.query(Source).filter(Source.is_active == True).all()
