from app.services import game_service, player_service

__all__ = ["game_service", "player_service"]


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
