from fastapi import FastAPI

from app.core.errors import register_exception_handlers
from app.database import Base, engine
from app.routers import games, players

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Number Guessing Game API", version="1.0.0")

# Register exception handlers
register_exception_handlers(app)

app.include_router(players.router)
app.include_router(games.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
