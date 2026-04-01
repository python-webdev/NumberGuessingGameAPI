import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models.player import Player as PlayerModel
from app.schemas.player import TokenData

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def create_access_token(data: TokenData) -> str:
    to_encode = data.model_dump()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)  # type: ignore[reportUnknownMemberType]


def get_current_player(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> PlayerModel:
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore[reportUnknownMemberType]
        token_data = TokenData.model_validate(payload)
        player_uuid = uuid.UUID(token_data.sub)
    except (InvalidTokenError, ValidationError, ValueError) as exc:
        raise credentials_exception from exc
    player = db.query(PlayerModel).filter(PlayerModel.id == player_uuid).first()
    if player is None:
        raise credentials_exception
    return player
