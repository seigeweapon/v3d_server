from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.models.background import Background
from app.schemas.background import BackgroundCreate, BackgroundRead
from app.utils.storage import generate_tos_post_form_data

router = APIRouter(prefix="/backgrounds", tags=["backgrounds"])


@router.get("/", response_model=List[BackgroundRead])
def list_backgrounds(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)
):
    return (
        db.query(Background)
        .filter(Background.owner_id == current_user.id)
        .order_by(Background.created_at.desc())
        .all()
    )


@router.post("/", response_model=BackgroundRead)
def create_background(
    background_in: BackgroundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    # 生成 TOS 对象 key：前缀 + UUID
    # 注意：对象存储的 key 不包含 schema，形如 "<prefix>/<uuid>"
    key_prefix = settings.tos_background_prefix.rstrip("/") + "/"
    object_key = f"{key_prefix}{uuid4()}"

    # 用于写入数据库/展示的 tos_path，可包含 bucket 信息
    tos_path = f"tos://{settings.tos_bucket}/{object_key}"

    # 创建时状态默认为 uploading
    background = Background(
        owner_id=current_user.id,
        camera_count=background_in.camera_count,
        tos_path=tos_path,
        notes=background_in.notes,
        status="uploading",
    )
    db.add(background)
    db.commit()
    db.refresh(background)

    # 为前端生成 PostObject 表单数据（用于浏览器表单上传，可绕过 CORS）
    post_form_data = generate_tos_post_form_data(object_key)

    # 将 post_form_data 附加到响应模型上（Pydantic 会忽略 ORM 中不存在的字段）
    return BackgroundRead(
        id=background.id,
        owner_id=background.owner_id,
        camera_count=background.camera_count,
        tos_path=background.tos_path,
        notes=background.notes,
        status=background.status,
        created_at=background.created_at,
        upload_url=None,  # 不再使用 PUT URL
        post_form_data=post_form_data,  # 使用 PostObject 表单数据
    )


@router.post("/{background_id}/ready", response_model=BackgroundRead)
def mark_background_ready(
    background_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """前端在确认所有文件上传完成后调用，将背景记录标记为 ready。"""
    background = (
        db.query(Background)
        .filter(Background.id == background_id, Background.owner_id == current_user.id)
        .first()
    )
    if not background:
        raise HTTPException(status_code=404, detail="Background not found")

    # TODO: 未来可以在这里对 TOS 做一次 HEAD Object 校验，确认对象存在
    background.status = "ready"
    db.add(background)
    db.commit()
    db.refresh(background)
    return background


@router.get("/{background_id}", response_model=BackgroundRead)
def get_background(
    background_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    background = db.query(Background).filter(
        Background.id == background_id,
        Background.owner_id == current_user.id
    ).first()
    if not background:
        raise HTTPException(status_code=404, detail="Background not found")
    return background


@router.delete("/{background_id}")
def delete_background(
    background_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    background = db.query(Background).filter(
        Background.id == background_id,
        Background.owner_id == current_user.id
    ).first()
    if not background:
        raise HTTPException(status_code=404, detail="Background not found")
    db.delete(background)
    db.commit()
    return {"ok": True}

