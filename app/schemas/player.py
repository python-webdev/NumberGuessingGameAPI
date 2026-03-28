import re
from datetime import datetime
from typing import Optional

from pydantic import UUID4, BaseModel, field_validator


def validate_username(value: str) -> str:
    username = value.strip()
    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters long")
    if len(username) > 50:
        raise ValueError("Username must be at most 50 characters long")
    if not re.fullmatch(r"[A-Za-z0-9_]+", username):
        raise ValueError("Username must contain only letters, numbers, and underscores")
    return username


class PlayerCreate(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def username_must_be_valid(cls, username: str) -> str:
        return validate_username(username)


class PlayerUpdate(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def username_must_be_valid(cls, username: str) -> str:
        return validate_username(username)


class PlayerResponse(BaseModel):
    id: UUID4
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PlayerSearchParams(BaseModel):
    username: Optional[str] = None  # Filter by username (partial match)
