from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel


class BackgroundBase(BaseModel):
    camera_count: int
    notes: Optional[str] = None


class BackgroundCreate(BackgroundBase):
    pass


class BackgroundRead(BaseModel):
    camera_count: int
    tos_path: str
    notes: Optional[str] = None
    id: int
    owner_id: int
    status: str
    created_at: datetime
    # 仅在创建时返回的预签名上传 URL（PUT 方式，已废弃）
    upload_url: Optional[str] = None
    # 仅在创建时返回的 PostObject 表单数据（用于浏览器表单上传，可绕过 CORS）
    post_form_data: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

