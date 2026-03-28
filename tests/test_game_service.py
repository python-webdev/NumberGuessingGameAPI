import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.game import Game
from app.schemas.player import PlayerCreate
from app.services.game_service import create_game, submit_guess
from app.services.player_service import create_player


class TestCreateGame:
    def test_create_game_successfully(self, db: Session) -> None:
        player = create_player(db, payload=PlayerCreate(username="game_creator"))
        game = create_game(db, str(player.id))
        assert game.status == "active"
        assert game.attempts_used == 0

    def test_raises_if_active_game_exists(self, db: Session) -> None:
        player = create_player(db, payload=PlayerCreate(username="active_game_player"))
        create_game(db, str(player.id))
        with pytest.raises(HTTPException) as exc_info:
            create_game(db, str(player.id))
        assert exc_info.value.status_code == 400
        assert (
            exc_info.value.detail
            == "You already have an active game. Please finish it first."
        )


class TestSubmitGuess:
    def test_returns_too_low(self, db: Session) -> None:
        player = create_player(db, payload=PlayerCreate(username="guess_tester"))
        game = create_game(db, str(player.id))
        # Manually set the secret number for testing
        game_in_db = db.query(Game).filter(Game.id == game.id).first()
        assert game_in_db is not None
        game_in_db.secret_number = 50
        db.commit()

        guess_response = submit_guess(db, game_id=str(game.id), value=30)
        assert guess_response.result == "too low"

    def test_returns_too_high(self, db: Session) -> None:
        player = create_player(db, payload=PlayerCreate(username="guess_tester2"))
        game = create_game(db, str(player.id))
        # Manually set the secret number for testing
        game_in_db = db.query(Game).filter(Game.id == game.id).first()
        assert game_in_db is not None
        game_in_db.secret_number = 50
        db.commit()

        guess_response = submit_guess(db, game_id=str(game.id), value=70)
        assert guess_response.result == "too high"

    def test_correct_guess_wins_game(self, db: Session) -> None:
        player = create_player(db, payload=PlayerCreate(username="winner_tester"))
        game = create_game(db, str(player.id))
        # Manually set the secret number for testing
        game_in_db = db.query(Game).filter(Game.id == game.id).first()
        assert game_in_db is not None
        game_in_db.secret_number = 50
        db.commit()

        guess_response = submit_guess(db, game_id=str(game.id), value=50)
        assert guess_response.result == "correct"
        # Verify game status is updated to "won"
        updated_game = db.query(Game).filter(Game.id == game.id).first()
        assert updated_game is not None
        assert updated_game.status == "won"

    def test_reveals_secret_number_on_win(self, db: Session) -> None:
        player = create_player(
            db, payload=PlayerCreate(username="secret_reveal_tester")
        )
        game = create_game(db, str(player.id))
        # Manually set the secret number for testing
        game_in_db = db.query(Game).filter(Game.id == game.id).first()
        assert game_in_db is not None
        game_in_db.secret_number = 42
        db.commit()

        guess_response = submit_guess(db, game_id=str(game.id), value=42)
        assert guess_response.result == "correct"
        assert guess_response.secret_number == 42

    def test_secret_number_hidden_during_active_game(self, db: Session) -> None:
        player = create_player(
            db, payload=PlayerCreate(username="secret_hidden_tester")
        )
        game = create_game(db, str(player.id))
        # Manually set the secret number for testing
        game_in_db = db.query(Game).filter(Game.id == game.id).first()
        assert game_in_db is not None
        game_in_db.secret_number = 99
        db.commit()

        guess_response = submit_guess(db, game_id=str(game.id), value=50)
        assert guess_response.result == "too low"
        assert guess_response.secret_number is None

    def test_game_lost_when_attemps_exhausted(self, db: Session) -> None:
        player = create_player(db, payload=PlayerCreate(username="loser_tester"))
        game = create_game(db, str(player.id))
        # Manually set the secret number and max attempts for testing
        game_in_db = db.query(Game).filter(Game.id == game.id).first()
        assert game_in_db is not None
        game_in_db.secret_number = 10
        game_in_db.max_attempts = 2
        db.commit()

        submit_guess(db, game_id=str(game.id), value=1)  # Attempt 1
        submit_guess(db, game_id=str(game.id), value=2)  # Attempt 2 - should lose

        updated_game = db.query(Game).filter(Game.id == game.id).first()
        assert updated_game is not None
        assert updated_game.status == "lost"

    # Invariant tests - these must never break
    def test_cannot_guess_on_finished_game(self, db: Session) -> None:
        player = create_player(
            db, payload=PlayerCreate(username="finished_game_tester")
        )
        game = create_game(db, str(player.id))
        # Manually set the secret number and max attempts for testing
        game_in_db = db.query(Game).filter(Game.id == game.id).first()
        assert game_in_db is not None
        game_in_db.secret_number = 5
        game_in_db.max_attempts = 1
        db.commit()

        submit_guess(db, game_id=str(game.id), value=1)  # Attempt 1 - should lose

        with pytest.raises(HTTPException) as exc_info:
            submit_guess(db, game_id=str(game.id), value=5)  # Attempt on finished game
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Game is already finished."

    def test_attempts_increment_on_each_guess(self, db: Session) -> None:
        player = create_player(
            db, payload=PlayerCreate(username="attempts_increment_tester")
        )
        game = create_game(db, str(player.id))
        # Manually set the secret number for testing
        game_in_db = db.query(Game).filter(Game.id == game.id).first()
        assert game_in_db is not None
        game_in_db.secret_number = 20
        db.commit()

        submit_guess(db, game_id=str(game.id), value=10)  # Attempt 1
        submit_guess(db, game_id=str(game.id), value=15)  # Attempt 2

        updated_game = db.query(Game).filter(Game.id == game.id).first()
        assert updated_game is not None
        assert updated_game.attempts_used == 2
