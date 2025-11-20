from pydantic import BaseSettings, AnyHttpUrl
from typing import List, Optional


class Settings(BaseSettings):
    app_name: str = "Video Processing Service"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "changeme"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"

    database_url: str = "sqlite:///./app.db"

    s3_endpoint: Optional[AnyHttpUrl] = None
    s3_bucket: str = "videos"

    cors_origins: List[AnyHttpUrl] = []

    class Config:
        env_file = ".env"


settings = Settings()
