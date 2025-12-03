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
from app.utils.storage import generate_tos_post_form_data, delete_tos_objects_by_prefix

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
    # 生成 UUID 作为目录名
    uuid_dir = str(uuid4())
    
    # 生成 TOS 路径前缀：前缀 + UUID（用于数据库存储，不包含文件名）
    # 注意：对象存储的 key 不包含 schema，形如 "<prefix>/<uuid>"
    key_prefix = settings.tos_background_prefix.rstrip("/") + "/"
    uuid_path = f"{key_prefix}{uuid_dir}"

    # 用于写入数据库/展示的 tos_path，可包含 bucket 信息（只到 UUID 目录，不包含文件名）
    tos_path = f"tos://{settings.tos_bucket}/{uuid_path}"

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

    # 为每个文件生成 PostObject 表单数据
    # 如果提供了文件信息列表，为每个文件生成表单数据；否则生成一个占位表单数据
    post_form_data_list = []
    if background_in.file_infos:
        for file_info in background_in.file_infos:
            filename = file_info.get("name", "unknown")
            content_type = file_info.get("type")  # MIME 类型，如 "image/png"
            # 对象 key 格式：{prefix}/{uuid}/{文件名}
            object_key = f"{uuid_path}/{filename}"
            post_form_data = generate_tos_post_form_data(object_key, content_type=content_type)
            post_form_data_list.append(post_form_data)
    else:
        # 如果没有提供文件信息，生成一个占位表单数据（兼容旧代码）
        object_key = f"{uuid_path}/placeholder"
        post_form_data = generate_tos_post_form_data(object_key)
        post_form_data_list.append(post_form_data)

    # 将 post_form_data_list 附加到响应模型上（Pydantic 会忽略 ORM 中不存在的字段）
    return BackgroundRead(
        id=background.id,
        owner_id=background.owner_id,
        camera_count=background.camera_count,
        tos_path=background.tos_path,
        notes=background.notes,
        status=background.status,
        created_at=background.created_at,
        upload_url=None,  # 不再使用 PUT URL
        post_form_data_list=post_form_data_list,  # 使用 PostObject 表单数据列表
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
    """
    删除背景记录，同时删除 TOS 上的所有相关文件。
    """
    background = db.query(Background).filter(
        Background.id == background_id,
        Background.owner_id == current_user.id
    ).first()
    if not background:
        raise HTTPException(status_code=404, detail="Background not found")
    
    # 从 tos_path 中提取路径前缀（去掉 tos://bucket/ 前缀）
    # tos_path 格式: tos://{bucket}/{prefix}/{uuid}
    tos_path = background.tos_path
    if tos_path.startswith("tos://"):
        path_without_schema = tos_path[6:]  # 去掉 "tos://"
        # 提取 bucket 后面的路径
        if "/" in path_without_schema:
            bucket, path_after_bucket = path_without_schema.split("/", 1)
            uuid_path = path_after_bucket
        else:
            raise HTTPException(status_code=400, detail="Invalid tos_path format")
    else:
        uuid_path = tos_path
    
    # 确保路径以 / 结尾，以便列出该目录下的所有文件
    prefix = uuid_path.rstrip("/") + "/"
    
    # 删除操作：先删除 TOS 文件，再删除数据库记录
    # 将两个操作分开处理，确保能正确区分 TOS 操作失败和数据库操作失败
    
    # 第一步：删除 TOS 上的所有文件
    # 如果失败，抛出异常，阻止数据库记录的删除，避免产生孤儿文件
    try:
        delete_tos_objects_by_prefix(prefix)
    except RuntimeError as e:
        # TOS 文件删除失败（包括列出对象失败和删除对象失败）
        # 阻止数据库记录删除，确保数据一致性
        import logging
        logging.error(f"删除 TOS 文件失败 (prefix={prefix}): {e}")
        raise HTTPException(
            status_code=500,
            detail=f"删除 TOS 文件失败: {str(e)}。数据库记录未删除，请稍后重试。"
        )
    
    # 第二步：只有在 TOS 文件删除成功后才删除数据库记录
    # 单独处理数据库操作异常，避免与 TOS 操作异常混淆
    try:
        db.delete(background)
        db.commit()
    except Exception as e:
        # 数据库操作失败
        # 注意：此时 TOS 文件已被删除，但数据库记录删除失败
        import logging
        logging.error(f"删除数据库记录失败 (background_id={background_id}): {e}")
        # 回滚数据库事务（如果还在事务中）
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"删除数据库记录失败: {str(e)}。TOS 文件已被删除，请检查并手动清理数据库记录。"
        )
    
    return {"ok": True}

