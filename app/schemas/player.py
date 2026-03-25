from datetime import datetime

from pydantic import UUID4, BaseModel, field_validator


class PlayerCreate(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def username_must_be_valid(cls, username: str) -> str:
        username = username.strip()
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(username) > 20:
            raise ValueError("Username must be at most 20 characters long")
        if not username.isalnum():
            raise ValueError("Username must be alphanumeric only")
        return username


class PlayerResponse(BaseModel):
    id: UUID4
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}
