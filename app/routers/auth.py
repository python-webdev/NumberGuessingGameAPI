from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.database import get_db
from app.models.player import Player
from app.schemas.player import (
    PlayerCreate,
    PlayerResponse,
    TokenData,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", response_model=PlayerResponse, status_code=201)
def register(
    payload: PlayerCreate, db: Session = Depends(get_db)
) -> PlayerResponse:
    existing = (
        db.query(Player).filter(Player.username == payload.username).first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    player = Player(
        username=payload.username,
        password=pwd_context.hash(payload.password),
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return PlayerResponse.model_validate(player)


@router.post("/token", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    player = (
        db.query(Player).filter(Player.username == form_data.username).first()
    )

    if not player or not pwd_context.verify(
        form_data.password, player.password
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(data=TokenData(sub=str(player.id)))
    return TokenResponse(access_token=token, token_type="bearer")
