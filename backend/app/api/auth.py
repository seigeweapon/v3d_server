from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.database import get_db
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册接口。
    注意：为了安全，注册接口不允许设置 is_superuser，所有注册用户都是普通用户。
    如果需要创建管理员账户，请使用管理员用户管理接口 POST /api/v1/users/（需要管理员权限）。
    如果是第一个用户且系统中没有管理员，可以自动设置为管理员（用于初始化系统）。
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 检查是否已有管理员用户
    has_superuser = db.query(User).filter(User.is_superuser == True).first() is not None
    
    # 如果是第一个用户且没有管理员，自动设置为管理员
    # 否则，忽略请求中的 is_superuser，强制设置为普通用户（安全考虑）
    is_first_user = db.query(User).count() == 0
    
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_superuser=(is_first_user and not has_superuser),  # 只有第一个用户且没有管理员时，才设置为管理员
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = deps.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    # 确保返回正确的用户ID（用于调试）
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.refresh_token_expire_minutes),
    )
    return Token(access_token=access_token, refresh_token=refresh_token)
