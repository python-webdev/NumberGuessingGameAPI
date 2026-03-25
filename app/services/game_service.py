import random

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.game import Game
from app.models.guess import Guess
from app.schemas.guess import GuessResponse


def create_game(db: Session, player_id: str) -> Game:
    # Check to see if the player already has an active game
    active_game = (
        db.query(Game)
        .filter(Game.player_id == player_id, Game.status == "active")
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
        player_id=player_id,
        secret_number=secret_number,
        max_attempts=settings.MAX_ATTEMPTS,
        attempts_used=0,
        status="active",
    )

    db.add(game)
    db.commit()
    db.refresh(game)
    return game


def submit_guess(db: Session, game_id: str, value: int) -> GuessResponse:
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Invariant 1: cannot guess on a finished game
    if game.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Game is already {game.status}. No more guesses allowed.",
        )

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

    # Update game state    game.attempts_used += 1
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


def get_game(db: Session, game_id: str) -> Game:
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


def get_player_games(db: Session, player_id: str) -> list[Game]:
    return (
        db.query(Game)
        .filter(Game.player_id == player_id)
        .order_by(Game.created_at.desc())
        .all()
    )
