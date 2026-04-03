# Number Guessing Game API

A REST API for a number guessing game where players can register, start games, and submit guesses. Built with FastAPI and PostgreSQL.

## Features

- Player registration and JWT authentication
- Game creation with configurable number ranges and attempt limits
- Guess submission with feedback (`too_low`, `too_high`, `correct`)
- Game history with pagination, filtering, and sorting
- Rate limiting on sensitive endpoints
- Health check endpoint with database status

## Tech Stack

- **Framework:** FastAPI 0.111.0
- **Server:** Uvicorn (ASGI)
- **Database:** PostgreSQL 16 + SQLAlchemy 2.0 + Alembic migrations
- **Auth:** PyJWT (HS256) + bcrypt password hashing
- **Rate limiting:** slowapi
- **Containerization:** Docker + Docker Compose
- **Testing:** pytest + httpx + pytest-cov
- **Linting/Formatting:** ruff, black, mypy

## Project Structure

```
app/
├── core/           # Config, security, middleware, rate limiting, logging
├── models/         # SQLAlchemy ORM models (Player, Game, Guess)
├── routers/        # API route handlers (auth, games, players)
├── schemas/        # Pydantic request/response schemas
├── services/       # Business logic (game_service, player_service)
├── database.py     # SQLAlchemy setup and session management
└── main.py         # FastAPI app entry point

migrations/         # Alembic database migrations
tests/              # pytest test suite
```

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Run with Docker Compose

```bash
docker-compose up
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env .env.local
# Edit .env.local with your database URL and secret key

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

| Variable                    | Default                                              | Description                        |
|-----------------------------|------------------------------------------------------|------------------------------------|
| `DATABASE_URL`              | `postgresql://web@localhost:5432/guessing_game`      | PostgreSQL connection string        |
| `SECRET_KEY`                | *(required)*                                         | JWT signing secret                  |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                                               | JWT token lifetime in minutes       |
| `MAX_ATTEMPTS`              | `10`                                                 | Maximum guesses per game            |
| `NUMBER_RANGE_MIN`          | `1`                                                  | Minimum value for the secret number |
| `NUMBER_RANGE_MAX`          | `100`                                                | Maximum value for the secret number |

## API Reference

Base path: `/api/v1`

### Authentication

| Method | Endpoint              | Description                        | Auth |
|--------|-----------------------|------------------------------------|------|
| POST   | `/auth/register`      | Register a new player              | No   |
| POST   | `/auth/token`         | Login and receive a JWT token      | No   |

### Players

| Method | Endpoint              | Description                                       | Auth |
|--------|-----------------------|---------------------------------------------------|------|
| POST   | `/players/`           | Create a player *(10 req/min)*                    | No   |
| GET    | `/players/`           | Search players by username (paginated)            | No   |
| GET    | `/players/{id}`       | Get player profile                                | No   |
| PUT    | `/players/{id}`       | Update player username                            | Yes  |
| GET    | `/players/{id}/games` | Get player game history (paginated, filterable)   | Yes  |

### Games

| Method | Endpoint                  | Description                                       | Auth |
|--------|---------------------------|---------------------------------------------------|------|
| POST   | `/games/`                 | Start a new game (one active game per player)     | Yes  |
| GET    | `/games/{id}`             | Get game state (secret number never exposed)      | Yes  |
| POST   | `/games/{id}/guesses`     | Submit a guess *(30 req/min)*                     | Yes  |

### Health

| Method | Endpoint  | Description                          |
|--------|-----------|--------------------------------------|
| GET    | `/health` | API health check with database status |

## Running Tests

```bash
# Run all tests with coverage
pytest -v --cov=app --cov-report=term-missing
```

By default tests use an in-memory SQLite database. To run against PostgreSQL:

```bash
export TEST_DATABASE_URL=postgresql://postgres:password@localhost:5433/guessing_game_test
pytest -v
```

A dedicated PostgreSQL test container is available via Docker Compose on port `5433`.

## CI/CD

GitHub Actions runs on every push to `main` and on pull requests:

1. **Lint** — `ruff`, `black --check`, `mypy`
2. **Test** — `pytest` against a PostgreSQL 16 service container
3. **Docker Build** — verifies the image builds successfully

## License

MIT
