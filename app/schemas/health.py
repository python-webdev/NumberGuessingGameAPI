from pydantic import BaseModel

from app.schemas.database import DatabaseCheck


class HealthResponse(BaseModel):
    # Health check response schema
    status: str
    version: str
    checks: dict[str, DatabaseCheck]
