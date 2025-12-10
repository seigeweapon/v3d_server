from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel


class VideoBase(BaseModel):
    studio: str
    producer: str
    production: str
    action: str
    camera_count: int
    prime_camera_number: int
    frame_count: int
    frame_rate: float
    frame_width: int
    frame_height: int
    video_format: str
    tos_path: str
    status: str


class VideoCreate(VideoBase):
    pass


class VideoUpload(BaseModel):
    """视频上传请求，包含基本信息（不含元数据）和文件信息"""
    studio: str
    producer: str
    production: str
    action: str
    # 文件信息列表，包含文件名和 MIME 类型
    # 格式: [{"name": "video.mp4", "type": "video/mp4"}, {"name": "bg.png", "type": "image/png"}, {"name": "calib.json", "type": "application/json"}]
    file_infos: Optional[List[Dict[str, str]]] = None


class VideoRead(BaseModel):
    studio: str
    producer: str
    production: str
    action: str
    camera_count: int
    prime_camera_number: int
    frame_count: int
    frame_rate: float
    frame_width: int
    frame_height: int
    video_format: str
    tos_path: str
    status: str
    id: int
    owner_id: int
    created_at: datetime
    # 仅在创建时返回的 PostObject 表单数据（用于浏览器表单上传，可绕过 CORS）
    # 如果上传多个文件，这是一个列表，每个元素对应一个文件的表单数据
    post_form_data_list: Optional[List[Dict[str, Any]]] = None

    class Config:
        orm_mode = True
