from pydantic import BaseSettings, AnyHttpUrl, Field
from typing import List, Optional


class Settings(BaseSettings):
    app_name: str = "Video Processing Service"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "changeme"
    access_token_expire_minutes: int = 60 * 24  # 24小时
    refresh_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"

    database_url: str = "sqlite:///./app.db"

    # 兼容未来对象存储配置（目前用于 TOS）
    s3_endpoint: Optional[AnyHttpUrl] = None
    s3_bucket: str = "videos"
    
    # TOS (对象存储) 认证信息
    tos_access_key: Optional[str] = None
    tos_secret_key: Optional[str] = None
    tos_region: Optional[str] = None  # 可选：TOS 区域
    tos_endpoint: Optional[str] = None  # 例如: "tos-cn-beijing.volces.com"
    tos_bucket: str = "videos"  # 默认桶名，可在 .env 中覆盖
    # TOS key 前缀，仅使用 TOS_VIDEO_KEY_PREFIX
    tos_key_prefix: str = Field(
        "fv-data/tests",
        env="TOS_VIDEO_KEY_PREFIX",
        description="TOS key 前缀，格式：<prefix>/<uuid>/<category>",
    )

    cors_origins: List[AnyHttpUrl] = []

    class Config:
        env_file = ".env"


settings = Settings()
