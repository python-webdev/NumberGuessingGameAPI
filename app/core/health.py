import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def check_database(db: Session) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except SQLAlchemyError as e:
        logger.error("Database connection error: %s", e)
        return {"status": "unhealthy", "error": str(e)}
