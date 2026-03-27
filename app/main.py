from fastapi import FastAPI

from app.core.errors import register_exception_handlers
from app.database import Base, engine
from app.routers import games, players

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Number Guessing Game API", version="1.1")

# Register exception handlers
register_exception_handlers(app)

app.include_router(players.router, prefix="/api/v1.1")
app.include_router(games.router, prefix="/api/v1.1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
