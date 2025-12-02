from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CalibrationBase(BaseModel):
    camera_count: int
    tos_path: str
    notes: Optional[str] = None


class CalibrationCreate(CalibrationBase):
    pass


class CalibrationRead(CalibrationBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True

