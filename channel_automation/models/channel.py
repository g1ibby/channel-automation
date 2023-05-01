from typing import Optional

from sqlmodel import Field, SQLModel


class ChannelInfo(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str = Field()
