from .game_service import create_game, get_game, get_player_games, submit_guess
from .player_service import create_player, get_player_by_id

__all__ = [
    "create_game",
    "submit_guess",
    "get_game",
    "get_player_games",
    "create_player",
    "get_player_by_id",
]


## How the Layers Connect
""" 
  HTTP Request
     ↓
  Router         → validates shape (Pydantic schema)
     ↓
  Service        → validates business rules, changes state
     ↓
  Model          → talks to database
     ↓
  Database       → enforces constraints
  """
