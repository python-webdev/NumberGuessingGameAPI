from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.player import Player
from app.schemas.player import PlayerCreate, PlayerResponse


def create_player(db: Session, payload: PlayerCreate) -> PlayerResponse:
    # Check if the username already exists
    existing_player = (
        db.query(Player).filter(Player.username == payload.username).first()
    )
    if existing_player:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_player = Player(username=payload.username)
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    return PlayerResponse.model_validate(new_player)


def get_player_by_id(db: Session, player_id: str) -> PlayerResponse:
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return PlayerResponse.model_validate(player)
