from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VideoBase(BaseModel):
    filename: str
    description: Optional[str] = None


class VideoUpload(VideoBase):
    pass


class VideoRead(VideoBase):
    id: int
    owner_id: int
    storage_path: str
    created_at: datetime

    class Config:
        orm_mode = True
