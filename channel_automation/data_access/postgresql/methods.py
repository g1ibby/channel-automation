from typing import List

from contextlib import contextmanager

from sqlmodel import Session, create_engine

from alembic import command
from alembic.config import Config
from channel_automation.interfaces.pg_repository_interface import IRepository
from channel_automation.models import ChannelInfo
from channel_automation.models.source import Source


class Repository(IRepository):
    def __init__(self, database_url: str):
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(alembic_cfg, "head")

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

    def add_channel(self, channel: ChannelInfo) -> ChannelInfo:
        with self._get_session() as session:
            existing_channel = (
                session.query(ChannelInfo)
                .filter(ChannelInfo.id == channel.id)
                .one_or_none()
            )
            if existing_channel:
                existing_channel.title = channel.title
            else:
                session.add(channel)
                existing_channel = channel

            session.commit()
            session.refresh(existing_channel)
            return existing_channel

    def remove_channel(self, channel_id: str) -> None:
        with self._get_session() as session:
            channel = (
                session.query(ChannelInfo)
                .filter(ChannelInfo.id == channel_id)
                .one_or_none()
            )
            if channel:
                session.delete(channel)
                session.commit()

    def get_all_channels(self) -> list[ChannelInfo]:
        with self._get_session() as session:
            return session.query(ChannelInfo).all()
