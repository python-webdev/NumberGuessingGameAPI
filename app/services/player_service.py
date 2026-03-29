import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.player import Player
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.player import (
    PlayerCreate,
    PlayerResponse,
    PlayerSearchParams,
    PlayerUpdate,
)


def create_player(db: Session, payload: PlayerCreate) -> PlayerResponse:
    # Check if the username already exists
    existing_player = (
        db.query(Player).filter(Player.username == payload.username).first()
    )
    if existing_player:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_player = Player(username=payload.username)
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    return PlayerResponse.model_validate(new_player)


def _to_uuid_or_none(value: str | uuid.UUID) -> uuid.UUID | None:
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def get_player(db: Session, player_id: str) -> PlayerResponse:
    normalized_id = _to_uuid_or_none(player_id)
    if normalized_id is None:
        raise HTTPException(status_code=404, detail="Player not found")

    player = db.query(Player).filter(Player.id == normalized_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return PlayerResponse.model_validate(player)


def search_players(
    db: Session, search: PlayerSearchParams, pagination: PaginationParams
) -> PaginatedResponse[PlayerResponse]:

    query = db.query(Player)

    if search.username:
        query = query.filter(Player.username.ilike(f"%{search.username}%"))

    total = query.count()

    players = (
        query.order_by(Player.created_at.desc())
        .offset((pagination.offset))
        .limit(pagination.page_size)
        .all()
    )

    return PaginatedResponse[PlayerResponse](
        items=[PlayerResponse.model_validate(player) for player in players],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=-(-total // pagination.page_size),
    )


def update_player(
    db: Session, player_id: str, payload: PlayerUpdate
) -> PlayerResponse:
    normalized_id = _to_uuid_or_none(player_id)
    if normalized_id is None:
        raise HTTPException(status_code=404, detail="Player not found")

    player = db.query(Player).filter(Player.id == normalized_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Check if the new username already exists for another player
    existing_player = (
        db.query(Player)
        .filter(Player.username == payload.username, Player.id != normalized_id)
        .first()
    )
    if existing_player:
        raise HTTPException(status_code=400, detail="Username already exists")

    player.username = payload.username
    db.commit()
    db.refresh(player)

    return PlayerResponse.model_validate(player)


def get_player_by_id(db: Session, player_id: str) -> PlayerResponse:
    normalized_id = _to_uuid_or_none(player_id)
    if normalized_id is None:
        raise HTTPException(status_code=404, detail="Player not found")

    player = db.query(Player).filter(Player.id == normalized_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return PlayerResponse.model_validate(player)
