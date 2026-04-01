from contextlib import asynccontextmanager
from typing import cast

from fastapi import Depends, FastAPI, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.core.errors import register_exception_handlers
from app.core.health import check_database
from app.core.logging import logger
from app.core.middleware import RequestLoggingMiddleware
from app.core.rate_limit import limiter
from app.database import get_db
from app.routers import auth, games, players
from app.schemas.database import DatabaseCheck
from app.schemas.health import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start-up event to check database connectivity
    logger.info("Application is starting up", extra={"version": app.version})
    yield
    # Shutdown event
    logger.info("Application is shutting down")


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    return _rate_limit_exceeded_handler(request, cast(RateLimitExceeded, exc))


app = FastAPI(
    title="Number Guessing Game API",
    version="1.1",
    lifespan=lifespan,
    description=""" A backend API for a number guessing game.

## Features
- Create players and manage their profiles
- Start games and submit guesses
- Track game history with pagination, filtering and sorting

## Rules
- Each game generates a secret number between 1 and 100
- Players have 10 attempts to guess correctly
- Responses tell you if your guess is too low, too high, or correct
    """,
    contact={
        "name": "Number Guessing Game API",
    },
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Middleware for logging requests
app.add_middleware(RequestLoggingMiddleware)

# Error handlers
register_exception_handlers(app)

app.include_router(auth.router, prefix="/api/v1")
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
