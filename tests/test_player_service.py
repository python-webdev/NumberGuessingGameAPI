import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.player import PlayerCreate, PlayerUpdate
from app.services.player_service import create_player, get_player, update_player


class TestCreatePlayer:
    def test_create_player_success(self, db: Session) -> None:
        player = create_player(db, payload=PlayerCreate(username="test_player"))
        assert player.username == "test_player"

    def test_raises_if_username_already_exists(self, db: Session) -> None:
        create_player(db, payload=PlayerCreate(username="duplicate_player"))
        with pytest.raises(HTTPException) as exc_info:
            create_player(db, payload=PlayerCreate(username="duplicate_player"))
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Username already exists"


class TestGetPlayer:
    def test_returns_player_if_exists(self, db: Session) -> None:
        created_player = create_player(
            db, payload=PlayerCreate(username="existing_player")
        )
        retrieved_player = get_player(db, player_id=str(created_player.id))
        assert retrieved_player.id == created_player.id
        assert retrieved_player.username == "existing_player"

    def test_raises_404_if_player_not_found(self, db: Session) -> None:
        with pytest.raises(HTTPException) as exc_info:
            get_player(db, player_id="nonexistent-id")
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Player not found"


class TestUpdatePlayer:
    def test_update_username_successfully(self, db: Session) -> None:
        player = create_player(db, payload=PlayerCreate(username="player_to_update"))
        updated_player = update_player(
            db,
            player_id=str(player.id),
            payload=PlayerUpdate(username="updated_player"),
        )
        assert updated_player.id == player.id
        assert updated_player.username == "updated_player"

    def test_raises_if_username_already_exists(self, db: Session) -> None:
        create_player(db, payload=PlayerCreate(username="player1"))
        player2 = create_player(db, payload=PlayerCreate(username="player2"))
        with pytest.raises(HTTPException) as exc_info:
            update_player(
                db,
                player_id=str(player2.id),
                payload=PlayerUpdate(username="player1"),
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Username already exists"
