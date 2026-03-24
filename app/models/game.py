import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    secret_number = Column(
        Integer, nullable=False
    )  # NEVER exposed in schema or API responses
    max_attempts = Column(Integer, nullable=False)
    attempts_used = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, won, lost
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Invariants enforced at DB level
    __table_args__ = (
        CheckConstraint("status IN ('active', 'won', 'lost')", name="valid_status"),
        CheckConstraint("attempts_used >= 0", name="attempts_non_negative"),
        CheckConstraint("attempts_used <= max_attempts", name="attempts_within_limit"),
        CheckConstraint("secret_number >= 1", name="secret_min"),
    )

    player = relationship("Player", back_populates="games")
    guesses = relationship("Guess", back_populates="game")
