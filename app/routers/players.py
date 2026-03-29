from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import services
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


@router.post("/", response_model=PlayerResponse, status_code=201)
def create_player(
    payload: PlayerCreate, db: Session = Depends(get_db)
) -> PlayerResponse:
    return services.player_service.create_player(db, payload)


@router.get("/", response_model=PaginatedResponse[PlayerResponse])
def search_players(
    username: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PlayerResponse]:
    search = PlayerSearchParams(username=username)
    pagination = PaginationParams(page=page, page_size=page_size)
    return services.player_service.search_players(db, search, pagination)


@router.get("/{id}", response_model=PlayerResponse)
def get_player(id: str, db: Session = Depends(get_db)) -> PlayerResponse:
    return services.player_service.get_player_by_id(db, id)


@router.get("/{id}/games", response_model=PaginatedResponse[GameResponse])
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


@router.put("/{id}", response_model=PlayerResponse)
def update_player(
    id: str,
    payload: PlayerUpdate,
    db: Session = Depends(get_db),
) -> PlayerResponse:
    return services.player_service.update_player(db, id, payload)
