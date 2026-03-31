from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app import services
from app.core.rate_limit import limiter
from app.database import get_db
from app.schemas.game import GameFilterParams, GameResponse, GameSortParams
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.player import (
    PlayerCreate,
    PlayerResponse,
    PlayerSearchParams,
    PlayerUpdate,
)

router = APIRouter(prefix="/players", tags=["players"])


@router.post(
    "/",
    response_model=PlayerResponse,
    status_code=201,
    summary="Create a new player",
    description=(
        "Create a new player with a unique username. "
        "Returns the created player profile."
    ),
)
@limiter.limit("10/minute")  # type: ignore[misc]
def create_player(
    payload: PlayerCreate,
    request: Request,  # pylint: disable=unused-argument
    db: Session = Depends(get_db),
) -> PlayerResponse:
    return services.player_service.create_player(db, payload)


@router.get(
    "/",
    response_model=PaginatedResponse[PlayerResponse],
    summary="Search players",
    description=("Search for players by username. Supports pagination."),
)
def search_players(
    username: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PlayerResponse]:
    search = PlayerSearchParams(username=username)
    pagination = PaginationParams(page=page, page_size=page_size)
    return services.player_service.search_players(db, search, pagination)


@router.get(
    "/{id}",
    response_model=PlayerResponse,
    summary="Get player by ID",
    description="Retrieve a player's profile by their unique ID.",
)
def get_player(id: str, db: Session = Depends(get_db)) -> PlayerResponse:
    return services.player_service.get_player_by_id(db, id)


@router.get(
    "/{id}/games",
    response_model=PaginatedResponse[GameResponse],
    summary="Get player's games",
    description="Retrieve a list of games played by a specific player.",
)
def get_player_games(
    id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[GameResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    filters = GameFilterParams(status=status)
    sort = GameSortParams(sort_by=sort_by, order=order)
    return services.game_service.get_player_games(
        db, id, pagination, filters, sort
    )


@router.put(
    "/{id}",
    response_model=PlayerResponse,
    summary="Update player",
    description="Update a player's profile by their unique ID.",
)
def update_player(
    id: str,
    payload: PlayerUpdate,
    db: Session = Depends(get_db),
) -> PlayerResponse:
    return services.player_service.update_player(db, id, payload)
