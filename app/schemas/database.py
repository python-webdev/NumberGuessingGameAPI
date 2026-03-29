from pydantic import BaseModel


class DatabaseCheck(BaseModel):
    # Database health check result
    status: str
