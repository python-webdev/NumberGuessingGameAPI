from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import register_exception_handlers
from app.core.health import check_database
from app.core.logging import logger
from app.core.middleware import RequestLoggingMiddleware
from app.database import get_db
from app.routers import games, players


class DatabaseCheck(BaseModel):
    # Database health check result
    status: str


class HealthResponse(BaseModel):
    # Health check response schema
    status: str
    version: str
    checks: dict[str, DatabaseCheck]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start-up event to check database connectivity
    logger.info("Application is starting up", extra={"version": app.version})
    yield
    # Shutdown event
    logger.info("Application is shutting down")


app = FastAPI(
    title="Number Guessing Game API", version="1.1", lifespan=lifespan
)

# Middleware for logging requests
app.add_middleware(RequestLoggingMiddleware)

# Error handlers
register_exception_handlers(app)

app.include_router(players.router, prefix="/api/v1")
app.include_router(games.router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", tags=["Health"], response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db_status = check_database(db)
        overall = "ok" if db_status["status"] == "healthy" else "degraded"
        return HealthResponse(
            status=overall,
            version=app.version,
            checks={"database": DatabaseCheck(status=db_status["status"])},
        )
    except SQLAlchemyError as e:
        logger.error("Database health check failed: %s", e)
        return HealthResponse(
            status="degraded",
            version=app.version,
            checks={"database": DatabaseCheck(status="unhealthy")},
        )
