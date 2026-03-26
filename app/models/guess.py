import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Guess(Base):
    __tablename__ = "guesses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("games.id"),
        nullable=False,
    )
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    # "too low", "too high", "correct"
    result: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint(
            "result IN ('too low', 'too high', 'correct')", name="valid_result"
        ),
        CheckConstraint("value >= 1", name="guess_min"),
    )

    game = relationship("Game", back_populates="guesses")
