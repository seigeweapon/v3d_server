from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobBase(BaseModel):
    video_id: int
    parameters: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobRead(JobBase):
    id: int
    owner_id: int
    status: str
    tos_path: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
