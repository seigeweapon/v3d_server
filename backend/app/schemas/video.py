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
    camera_count: Optional[int] = None  # 相机数（视频文件数量），如果不提供则从 file_infos 中推断
    # 视频元数据（从前端读取）
    frame_count: Optional[int] = None
    frame_rate: Optional[float] = None
    frame_width: Optional[int] = None
    frame_height: Optional[int] = None
    video_format: Optional[str] = None
    prime_camera_number: Optional[int] = None  # 主相机编号，默认为1
    # 文件信息列表，包含文件名和 MIME 类型
    # 格式: [{"name": "video.mp4", "type": "video/mp4"}, {"name": "bg.png", "type": "image/png"}, {"name": "calib.json", "type": "application/json"}]
    file_infos: Optional[List[Dict[str, str]]] = None


class VideoUpdate(BaseModel):
    """视频更新请求，只允许更新基本信息"""
    studio: Optional[str] = None
    producer: Optional[str] = None
    production: Optional[str] = None
    action: Optional[str] = None


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
    created_at: datetime
    # 仅在创建时返回的 PostObject 表单数据（用于浏览器表单上传，可绕过 CORS）
    # 如果上传多个文件，这是一个列表，每个元素对应一个文件的表单数据
    post_form_data_list: Optional[List[Dict[str, Any]]] = None

    class Config:
        orm_mode = True
