from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import get_password_hash, verify_password
from app.database import get_db
from app.models.user import User
from app.models.video import Video
from app.models.job import Job
from app.schemas.user import UserRead, UserUpdate, UserCreate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(deps.get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserRead)
def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """用户自己更新个人信息（需要旧密码验证才能修改密码）"""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    # 如果尝试修改密码，必须提供旧密码
    if user_update.password:
        if not user_update.old_password:
            raise HTTPException(status_code=400, detail="修改密码需要提供旧密码")
        # 验证旧密码
        if not verify_password(user_update.old_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="旧密码错误")
        # 更新密码
        current_user.hashed_password = get_password_hash(user_update.password)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


# 管理员专用的用户管理接口
@router.get("/", response_model=List[UserRead])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """获取所有用户列表（仅管理员）"""
    return db.query(User).all()


@router.post("/", response_model=UserRead)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """创建新用户（仅管理员）"""
    # 检查邮箱是否已存在
    existing_user_by_email = db.query(User).filter(User.email == user_in.email).first()
    if existing_user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 检查全名是否已存在（如果提供了全名）
    if user_in.full_name:
        existing_user_by_name = db.query(User).filter(User.full_name == user_in.full_name).first()
        if existing_user_by_name:
            raise HTTPException(status_code=400, detail="Full name already exists")
    
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        is_superuser=user_in.is_superuser if user_in.is_superuser is not None else False,  # 允许管理员指定是否为管理员
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """获取用户信息（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """更新用户信息（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 不允许将自己降级为普通用户（至少需要保留一个管理员）
    if user_update.is_superuser is not None and user_update.is_superuser == False:
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="不能将自己降级为普通用户")
    
    # 检查全名是否与其他用户重复（如果提供了全名且与当前不同）
    if user_update.full_name is not None and user_update.full_name != user.full_name:
        existing_user_by_name = db.query(User).filter(
            User.full_name == user_update.full_name,
            User.id != user_id  # 排除当前用户
        ).first()
        if existing_user_by_name:
            raise HTTPException(status_code=400, detail="Full name already exists")
        user.full_name = user_update.full_name
    
    # 管理员修改用户密码：如果提供了新密码，需要验证当前管理员的密码（作为身份确认）
    if user_update.password:
        if not user_update.old_password:
            raise HTTPException(status_code=400, detail="修改密码需要提供当前登录用户密码")
        # 验证当前管理员的密码（不是被修改用户的密码）
        if not verify_password(user_update.old_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="当前登录用户密码错误")
        # 更新被修改用户的密码
        user.hashed_password = get_password_hash(user_update.password)
    
    if user_update.is_superuser is not None:
        user.is_superuser = user_update.is_superuser
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """删除用户（仅管理员）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 不允许删除自己
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")
    
    # 检查是否有关联的视频数据
    video_count = db.query(Video).filter(Video.owner_id == user_id).count()
    
    # 检查是否有关联的任务数据
    job_count = db.query(Job).filter(Job.owner_id == user_id).count()
    
    # 如果有关联数据，提示用户
    if video_count > 0 or job_count > 0:
        error_detail = f"无法删除该用户，因为该用户还有关联数据："
        if video_count > 0:
            error_detail += f" {video_count} 个视频"
        if job_count > 0:
            if video_count > 0:
                error_detail += "，"
            error_detail += f" {job_count} 个任务"
        error_detail += "。请先删除所有关联数据后再删除用户。"
        raise HTTPException(status_code=400, detail=error_detail)
    
    db.delete(user)
    db.commit()
    return {"ok": True}
