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


class VideoUpdate(BaseModel):
    """视频更新请求，只允许更新基本信息"""
    studio: Optional[str] = None
    producer: Optional[str] = None
    production: Optional[str] = None
    action: Optional[str] = None


class VideoVisibilityUpdate(BaseModel):
    """视频可见性更新请求"""
    is_public: Optional[bool] = None
    visible_to_user_ids: Optional[List[int]] = None


class VideoDownloadRequest(BaseModel):
    """视频下载请求，指定要下载的文件类型"""
    file_types: List[str]  # 例如: ["video", "background", "calibration"]


class FileDownloadInfo(BaseModel):
    """文件下载信息"""
    object_key: str
    download_url: str
    filename: str
    file_type: str  # "video", "background", "calibration"


class VideoDownloadResponse(BaseModel):
    """视频下载响应，包含所有文件的下载URL"""
    files: List[FileDownloadInfo]


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
    owner_full_name: Optional[str] = None
    is_public: bool = False
    visible_to_user_ids: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
        
    @classmethod
    def from_orm(cls, obj):
        # 从owner关系中获取full_name
        instance = super().from_orm(obj)
        if hasattr(obj, 'owner') and obj.owner:
            instance.owner_full_name = obj.owner.full_name
        return instance
