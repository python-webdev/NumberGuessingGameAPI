from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    MAX_ATTEMPTS: int = 10
    NUMBER_RANGE_MIN: int = 1
    NUMBER_RANGE_MAX: int = 100

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
