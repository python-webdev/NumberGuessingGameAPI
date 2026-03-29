from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.schemas.game import GameCreate, GameResponse
from app.schemas.guess import GuessCreate, GuessResponse

router = APIRouter(prefix="/games", tags=["games"])


@router.post("/", response_model=GameResponse, status_code=201)
def create_game(
    payload: GameCreate, db: Session = Depends(get_db)
) -> GameResponse:
    return services.game_service.create_game(db, str(payload.player_id))


@router.get("/{id}", response_model=GameResponse)
def get_game(id: str, db: Session = Depends(get_db)) -> GameResponse:
    return services.game_service.get_game(db, id)


@router.post("/{id}/guesses", response_model=GuessResponse)
def submit_guess(
    id: str, payload: GuessCreate, db: Session = Depends(get_db)
) -> GuessResponse:
    response = services.game_service.submit_guess(db, id, payload.value)
    if response.result == "too low":
        response.result = "too_low"
    elif response.result == "too high":
        response.result = "too_high"
    return response
