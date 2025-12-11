from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    is_superuser: Optional[bool] = False  # 默认普通用户，仅用于管理员创建用户


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    old_password: Optional[str] = None  # 修改密码时需要提供旧密码（用户自己修改时）
    is_superuser: Optional[bool] = None  # 允许管理员修改用户权限


class UserRead(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        orm_mode = True
