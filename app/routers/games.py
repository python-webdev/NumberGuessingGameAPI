from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app import services
from app.core.rate_limit import limiter
from app.core.security import get_current_player
from app.database import get_db
from app.models.player import Player
from app.schemas.game import GameCreate, GameResponse
from app.schemas.guess import GuessCreate, GuessResponse

router = APIRouter(prefix="/games", tags=["games"])


@router.post(
    "/",
    response_model=GameResponse,
    status_code=201,
    summary="Start a new game",
    description=(
        "Start a new game for a player. Only one active game allowed at a time."
    ),
)
def create_game(
    payload: GameCreate,  # pylint: disable=unused-argument
    db: Session = Depends(get_db),
    current_player: Player = Depends(get_current_player),
) -> GameResponse:
    return services.game_service.create_game(db, str(current_player.id))


@router.get(
    "/{id}",
    response_model=GameResponse,
    summary="Get game by ID",
    description=(
        "Retrieve the current state of a game. Secret number is never exposed."
    ),
)
def get_game(id: str, db: Session = Depends(get_db)) -> GameResponse:
    return services.game_service.get_game(db, id)


@router.post(
    "/{id}/guesses",
    response_model=GuessResponse,
    summary="Submit a guess",
    description=(
        "Submit a guess for an active game. Returns too_low, too_high, "
        "or correct."
    ),
)
@limiter.limit("30/minute")  # type: ignore[misc]
def submit_guess(
    id: str,
    payload: GuessCreate,
    request: Request,  # pylint: disable=unused-argument
    db: Session = Depends(get_db),
    current_player: Player = Depends(get_current_player),  # pylint: disable=unused-argument
) -> GuessResponse:
    response = services.game_service.submit_guess(db, id, payload.value)
    if response.result == "too low":
        response.result = "too_low"
    elif response.result == "too high":
        response.result = "too_high"
    return response
