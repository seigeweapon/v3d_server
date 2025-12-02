from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BackgroundBase(BaseModel):
    camera_count: int
    tos_path: str
    notes: Optional[str] = None


class BackgroundCreate(BackgroundBase):
    pass


class BackgroundRead(BackgroundBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True

