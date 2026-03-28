import random
import uuid

from fastapi import HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.game import Game
from app.models.guess import Guess
from app.schemas.game import GameFilterParams, GameResponse, GameSortParams
from app.schemas.guess import GuessResponse
from app.schemas.pagination import PaginatedResponse, PaginationParams


def _to_uuid_or_none(value: str | uuid.UUID) -> uuid.UUID | None:
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def create_game(db: Session, player_id: str) -> GameResponse:
    normalized_player_id = _to_uuid_or_none(player_id)
    if normalized_player_id is None:
        raise HTTPException(status_code=404, detail="Player not found")

    # Check to see if the player already has an active game
    active_game = (
        db.query(Game)
        .filter(Game.player_id == normalized_player_id, Game.status == "active")
        .first()
    )
    if active_game:
        raise HTTPException(
            status_code=400,
            detail="You already have an active game. Please finish it first.",
        )

    # Secret number generation - never touch the API layer
    secret_number = random.randint(settings.NUMBER_RANGE_MIN, settings.NUMBER_RANGE_MAX)

    game = Game(
        player_id=normalized_player_id,
        secret_number=secret_number,
        max_attempts=settings.MAX_ATTEMPTS,
        attempts_used=0,
        status="active",
    )

    db.add(game)
    db.commit()
    db.refresh(game)
    return GameResponse.model_validate(game)


def submit_guess(db: Session, game_id: str, value: int) -> GuessResponse:
    normalized_game_id = _to_uuid_or_none(game_id)
    if normalized_game_id is None:
        raise HTTPException(status_code=404, detail="Game not found")

    game = db.query(Game).filter(Game.id == normalized_game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Invariant 1: cannot guess on a finished game
    if game.status != "active":
        raise HTTPException(status_code=400, detail="Game is already finished.")

    # Invariant 2: cannot exceed max attempts (double safety - DB constraint is first)
    if game.attempts_used >= game.max_attempts:
        raise HTTPException(status_code=400, detail="No attempts remaining.")

    # Evaluate the guess
    if value < game.secret_number:
        result = "too low"
    elif value > game.secret_number:
        result = "too high"
    else:
        result = "correct"

    # Record the game
    guess = Guess(game_id=game.id, value=value, result=result)
    db.add(guess)

    # Update game state
    game.attempts_used += 1

    if result == "correct":
        game.status = "won"
    elif game.attempts_used >= game.max_attempts:
        game.status = "lost"

    # Single commit - state changes atomatically
    db.commit()
    db.refresh(game)

    return GuessResponse(
        result=result,
        attempts_used=game.attempts_used,
        attempts_remaining=game.max_attempts - game.attempts_used,
        status=game.status,
        # Only reveal the secret number if the game is over
        secret_number=game.secret_number if game.status != "active" else None,
    )


def get_game(db: Session, game_id: str) -> GameResponse:
    normalized_game_id = _to_uuid_or_none(game_id)
    if normalized_game_id is None:
        raise HTTPException(status_code=404, detail="Game not found")

    game = db.query(Game).filter(Game.id == normalized_game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return GameResponse.model_validate(game)


def get_player_games(
    db: Session,
    player_id: str,
    pagination: PaginationParams,
    filters: GameFilterParams,
    sort: GameSortParams,
) -> PaginatedResponse[GameResponse]:
    normalized_player_id = _to_uuid_or_none(player_id)
    if normalized_player_id is None:
        return PaginatedResponse[GameResponse](
            items=[],
            total=0,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=0,
        )

    query = db.query(Game).filter(Game.player_id == normalized_player_id)

    if filters.status:
        if filters.status not in ["active", "won", "lost"]:
            raise HTTPException(status_code=400, detail="Invalid status filter")
        query = query.filter(Game.status == filters.status)

    ALLOWED_SORT_FIELDS: set[str] = {"created_at", "attempts_used", "status"}

    if sort.sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPException(status_code=400, detail=f"Cannot sort by {sort.sort_by}")

    sort_column = getattr(Game, sort.sort_by)
    query = query.order_by(
        desc(sort_column) if sort.order == "desc" else asc(sort_column)
    )

    total = query.count()

    games = query.offset(pagination.offset).limit(pagination.page_size).all()

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return PaginatedResponse[GameResponse](
        items=[GameResponse.model_validate(game) for game in games],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )
