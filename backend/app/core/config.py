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
    # TOS job key 前缀，用于任务结果存储
    tos_job_key_prefix: str = Field(
        "fv-data/jobs",
        env="TOS_JOB_KEY_PREFIX",
        description="TOS job key 前缀，格式：<bucket>/<prefix>/<uuid>/",
    )

    # Prodia / workflow execution service
    prodia_base_url: str = Field(
        "https://mediaapps-cn.byted.org",
        env="PRODIA_BASE_URL",
        description="Prodia 工作流基础 URL，例如 https://mediaapps-cn.byted.org",
    )
    prodia_api_key: Optional[str] = Field(
        default=None,
        env="PRODIA_API_KEY",
        description="Prodia Bearer Token，用于调用 workflow_execution 接口",
    )
    prodia_env: Optional[str] = Field(
        default=None,
        env="PRODIA_ENV",
        description="x-tt-env 头部，用于区分环境",
    )
    prodia_workflow_name: str = Field(
        "v3d/v3d_train_workflow",
        env="PRODIA_WORKFLOW_NAME",
        description="Prodia workflowName 参数",
    )
    prodia_workflow_dp_name: str = Field(
        "default",
        env="PRODIA_WORKFLOW_DP_NAME",
        description="Prodia workflowDpName 参数",
    )
    prodia_task_list: str = Field(
        "v3d/online",
        env="PRODIA_TASK_LIST",
        description="Prodia taskList 参数",
    )
    prodia_priority: int = Field(
        1,
        env="PRODIA_PRIORITY",
        description="Prodia priority 参数",
    )
    prodia_timeout_seconds: int = Field(
        60 * 60 * 24 * 3,
        env="PRODIA_TIMEOUT_SECONDS",
        description="Prodia timeout 秒数，默认 3 天",
    )
    prodia_callback_uri: Optional[AnyHttpUrl] = Field(
        default=None,
        env="PRODIA_CALLBACK_URI",
        description="可选的回调地址",
    )
    prodia_callback_args: Optional[str] = Field(
        default=None,
        env="PRODIA_CALLBACK_ARGS",
        description="回调参数，可选",
    )

    cors_origins: List[AnyHttpUrl] = []

    class Config:
        env_file = ".env"


settings = Settings()
