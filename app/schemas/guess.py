from pydantic import BaseModel, field_validator


class GuessCreate(BaseModel):
    value: int

    # Validate at API boundary - before it even touches the service layer
    @field_validator("value")
    @classmethod
    def value_must_be_in_range(cls, value: int) -> int:
        if value < 1 or value > 100:
            raise ValueError("Guess must be between 1 and 100")
        return value


class GuessResponse(BaseModel):
    result: str
    attempts_used: int
    attempts_remaining: int
    status: str
    secret_number: int | None

    model_config = {"from_attributes": True}
