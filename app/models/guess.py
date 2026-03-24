import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Guess(Base):
    __tablename__ = "guesses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    value = Column(Integer, nullable=False)
    result = Column(String(10), nullable=False)  # "too low", "too high", "correct"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    game = relationship("Game", back_populates="guesses")
