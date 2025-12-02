from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VideoBase(BaseModel):
    studio: str
    producer: str
    production: str
    action: str
    camera_count: int
    prime_camera_number: int
    background_id: int
    calibration_id: int
    frame_count: int
    frame_rate: float
    frame_width: int
    frame_height: int
    video_format: str
    tos_path: str


class VideoCreate(VideoBase):
    pass


class VideoRead(VideoBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True
