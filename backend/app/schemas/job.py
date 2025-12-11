from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class JobBase(BaseModel):
    video_id: int
    parameters: Optional[str] = None
    notes: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobRead(JobBase):
    id: int
    owner_id: int
    owner_full_name: Optional[str] = None
    status: str
    run_id: Optional[str] = None
    tos_path: Optional[str]
    notes: Optional[str]
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


class JobUpdate(BaseModel):
    """任务更新请求，目前只允许更新备注"""
    notes: Optional[str] = None


class JobVisibilityUpdate(BaseModel):
    """任务可见性更新请求"""
    is_public: Optional[bool] = None
    visible_to_user_ids: Optional[List[int]] = None
