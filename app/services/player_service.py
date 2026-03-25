from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.player import Player


def create_player(db: Session, username: str) -> Player:
    # Check if the username already exists
    existing_player = db.query(Player).filter(Player.username == username).first()
    if existing_player:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_player = Player(username=username)
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    return new_player


def get_player_by_id(db: Session, player_id: str) -> Player:
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
