from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.schemas.game import GameCreate, GameResponse
from app.schemas.guess import GuessCreate, GuessResponse

router = APIRouter(prefix="/games", tags=["games"])


@router.post("/", response_model=GameResponse, status_code=201)
def create_game(payload: GameCreate, db: Session = Depends(get_db)) -> GameResponse:
    return services.game_service.create_game(db, str(payload.player_id))


@router.get("/{game_id}", response_model=GameResponse)
def get_game(game_id: str, db: Session = Depends(get_db)) -> GameResponse:
    return services.game_service.get_game(db, game_id)


@router.post("/{game_id}/guesses", response_model=GuessResponse)
def submit_guess(
    game_id: str, payload: GuessCreate, db: Session = Depends(get_db)
) -> GuessResponse:
    return services.game_service.submit_guess(db, game_id, payload.value)
