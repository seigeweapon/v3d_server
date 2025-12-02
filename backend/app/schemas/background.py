from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel


class BackgroundBase(BaseModel):
    camera_count: int
    notes: Optional[str] = None


class BackgroundCreate(BackgroundBase):
    # 文件信息列表，包含文件名和 MIME 类型
    file_infos: Optional[List[Dict[str, str]]] = None  # 格式: [{"name": "file1.png", "type": "image/png"}, ...]


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
    # 如果上传多个文件，这是一个列表，每个元素对应一个文件的表单数据
    post_form_data_list: Optional[List[Dict[str, Any]]] = None

    class Config:
        orm_mode = True

