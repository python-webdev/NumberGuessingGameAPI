from datetime import datetime
from typing import Optional

from pydantic import UUID4, BaseModel


class GameCreate(BaseModel):
    player_id: Optional[UUID4] = None


class GameResponse(BaseModel):
    id: UUID4
    player_id: UUID4
    max_attempts: int
    attempts_used: int
    status: str
    created_at: datetime
    # Secret number is deliberately absent here - it never leaves the DB

    model_config = {"from_attributes": True}


class GameFilterParams(BaseModel):
    status: Optional[str] = (
        None  # Filter by game status ("active", "won", "lost")
    )


class GameSortParams(BaseModel):
    sort_by: str = "created_at"  # Default sorting field
    order: str = "desc"  # Default sorting order ("asc" or "desc")
