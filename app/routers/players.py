from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.schemas.game import GameFilterParams, GameResponse
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.player import PlayerCreate, PlayerResponse

router = APIRouter(prefix="/players", tags=["players"])


@router.post("/", response_model=PlayerResponse, status_code=201)
def create_player(
    payload: PlayerCreate, db: Session = Depends(get_db)
) -> PlayerResponse:
    return services.player_service.create_player(db, payload)


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(player_id: str, db: Session = Depends(get_db)) -> PlayerResponse:
    return services.player_service.get_player_by_id(db, player_id)


@router.get("/{player_id}/games", response_model=PaginatedResponse[GameResponse])
def get_player_games(
    player_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: str | None = Query(default=None, regex="^(active|won|lost)$"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[GameResponse]:
    pagination = PaginationParams(page=page, page_size=page_size)
    filters = GameFilterParams(status=status)
    return services.game_service.get_player_games(db, player_id, pagination, filters)
