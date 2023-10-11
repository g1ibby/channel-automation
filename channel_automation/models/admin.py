from sqlmodel import Field, SQLModel


class Admin(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_id: str = Field(
        index=True, unique=True
    )  # Assuming user_id is a unique identifier for each admin.
    name: str  # The name of the administrator (optional, but can be useful).
    is_active: bool = Field(
        default=True
    )  # Whether the admin is currently active or not.
