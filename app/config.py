from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    mode_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name:str = "ArchMind"
    debug: bool = False
    api_version: str = "v1"

    default_rps:int = 1000
    default_latency_ms: int = 50

@lru_cache
def get_settings() -> Settings:
    return Settings()