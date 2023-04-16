from typing import Optional

from sqlmodel import Field, SQLModel


class Source(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    link: str = Field()
    is_active: bool = Field(default=True)
