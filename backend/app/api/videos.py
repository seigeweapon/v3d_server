from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoCreate, VideoRead, VideoUpload
from app.utils.storage import generate_tos_post_form_data, delete_tos_objects_by_prefix

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/", response_model=List[VideoRead])
def list_videos(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)
):
    return db.query(Video).filter(Video.owner_id == current_user.id).all()


@router.post("/upload", response_model=VideoRead)
def upload_video(
    video_in: VideoUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """创建视频记录并生成 TOS 上传表单数据"""
    # 生成 UUID 作为目录名
    uuid_dir = str(uuid4())
    
    # 生成 TOS 路径前缀：<tos_key_prefix>/<uuid>/video（用于数据库存储，不包含文件名）
    # 注意：对象存储的 key 不包含 schema，形如 "<tos_key_prefix>/<uuid>/video"
    key_prefix = settings.tos_key_prefix.rstrip("/")
    uuid_path = f"{key_prefix}/{uuid_dir}/video"
    
    # 用于写入数据库/展示的 tos_path，可包含 bucket 信息（只到 UUID 目录，不包含文件名）
    tos_path = f"tos://{settings.tos_bucket}/{uuid_path}"
    
    # 创建视频记录（暂时不包含元数据，后续可以更新）
    # 注意：这里需要一些默认值，因为模型要求这些字段非空
    video = Video(
        owner_id=current_user.id,
        studio=video_in.studio,
        producer=video_in.producer,
        production=video_in.production,
        action=video_in.action,
        camera_count=1,  # 默认值，后续可更新
        prime_camera_number=1,  # 默认值，后续可更新
        frame_count=0,  # 默认值，后续可更新
        frame_rate=30.0,  # 默认值，后续可更新
        frame_width=1920,  # 默认值，后续可更新
        frame_height=1080,  # 默认值，后续可更新
        video_format="mp4",  # 默认值，后续可更新
        tos_path=tos_path,
        status="uploading",  # 初始状态为上传中
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    
    # 为每个文件生成 PostObject 表单数据
    # 文件顺序：0=视频文件, 1=背景文件, 2=标定文件（作为视频数据的组成部分）
    post_form_data_list = []
    if video_in.file_infos:
        key_prefix = settings.tos_key_prefix.rstrip("/")
        file_categories = ["video", "background", "calibration"]  # 文件类型分类，用于组织 TOS 路径
        
        for index, file_info in enumerate(video_in.file_infos):
            filename = file_info.get("name", "unknown")
            content_type = file_info.get("type")  # MIME 类型
            
            # 根据文件索引决定上传路径
            if index < len(file_categories):
                category = file_categories[index]
            else:
                # 如果文件数量超过3个，默认使用 video
                category = "video"
            
            # 对象 key 格式：<tos_key_prefix>/<uuid>/<category>/<filename>
            object_key = f"{key_prefix}/{uuid_dir}/{category}/{filename}"
            post_form_data = generate_tos_post_form_data(object_key, content_type=content_type)
            post_form_data_list.append(post_form_data)
    else:
        # 如果没有提供文件信息，生成一个占位表单数据
        object_key = f"{uuid_path}/placeholder"
        post_form_data = generate_tos_post_form_data(object_key)
        post_form_data_list.append(post_form_data)
    
    # 返回视频记录和上传表单数据
    return VideoRead(
        id=video.id,
        owner_id=video.owner_id,
        studio=video.studio,
        producer=video.producer,
        production=video.production,
        action=video.action,
        camera_count=video.camera_count,
        prime_camera_number=video.prime_camera_number,
        frame_count=video.frame_count,
        frame_rate=video.frame_rate,
        frame_width=video.frame_width,
        frame_height=video.frame_height,
        video_format=video.video_format,
        tos_path=video.tos_path,
        status=video.status,
        created_at=video.created_at,
        post_form_data_list=post_form_data_list,
    )


@router.post("/", response_model=VideoRead)
def create_video(
    video_in: VideoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """直接创建视频记录（用于测试或批量导入）"""
    video = Video(
        owner_id=current_user.id,
        **video_in.dict()
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return VideoRead(
        id=video.id,
        owner_id=video.owner_id,
        studio=video.studio,
        producer=video.producer,
        production=video.production,
        action=video.action,
        camera_count=video.camera_count,
        prime_camera_number=video.prime_camera_number,
        frame_count=video.frame_count,
        frame_rate=video.frame_rate,
        frame_width=video.frame_width,
        frame_height=video.frame_height,
        video_format=video.video_format,
        tos_path=video.tos_path,
        status=video.status,
        created_at=video.created_at,
    )


@router.get("/{video_id}", response_model=VideoRead)
def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    video = db.query(Video).filter(Video.id == video_id, Video.owner_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.delete("/{video_id}")
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    删除视频记录，同时删除 TOS 上的所有相关文件（包括 video、background、calibration 三个子目录）。
    注意：background 和 calibration 文件是作为视频数据的组成部分存储的，不是独立的表。
    """
    video = db.query(Video).filter(Video.id == video_id, Video.owner_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 从 tos_path 中提取路径前缀（去掉 tos://bucket/ 前缀）
    # tos_path 格式: tos://{bucket}/{prefix}/{uuid}/video
    tos_path = video.tos_path
    if tos_path.startswith("tos://"):
        path_without_schema = tos_path[6:]  # 去掉 "tos://"
        # 提取 bucket 后面的路径
        if "/" in path_without_schema:
            bucket, path_after_bucket = path_without_schema.split("/", 1)
            # 路径格式：<tos_key_prefix>/<uuid>/video，需要提取到 UUID 目录
            # 去掉最后的 /video 部分，得到 <tos_key_prefix>/<uuid>
            if path_after_bucket.endswith("/video"):
                uuid_path = path_after_bucket[:-6]  # 去掉 "/video"
            else:
                # 兼容旧格式，直接使用完整路径
                uuid_path = path_after_bucket
        else:
            raise HTTPException(status_code=400, detail="Invalid tos_path format")
    else:
        uuid_path = tos_path
    
    # 确保路径以 / 结尾，以便列出该目录下的所有文件（包括 video、background、calibration 子目录）
    prefix = uuid_path.rstrip("/") + "/"
    
    # 删除操作：先删除 TOS 文件，再删除数据库记录
    # 将两个操作分开处理，确保能正确区分 TOS 操作失败和数据库操作失败
    
    # 第一步：删除 TOS 上的所有文件（包括 video、background、calibration 三个子目录）
    # 注意：background 和 calibration 文件是作为视频数据的组成部分存储的
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
        db.delete(video)
        db.commit()
    except Exception as e:
        # 数据库操作失败
        # 注意：此时 TOS 文件已被删除，但数据库记录删除失败
        import logging
        logging.error(f"删除数据库记录失败 (video_id={video_id}): {e}")
        # 回滚数据库事务（如果还在事务中）
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"删除数据库记录失败: {str(e)}。TOS 文件已被删除，请检查并手动清理数据库记录。"
        )
    
    return {"ok": True}


@router.post("/{video_id}/ready", response_model=VideoRead)
def mark_video_ready(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """前端在确认所有文件上传完成后调用，将视频记录标记为 ready。"""
    video = db.query(Video).filter(Video.id == video_id, Video.owner_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # TODO: 未来可以在这里对 TOS 做一次 HEAD Object 校验，确认对象存在
    video.status = "ready"
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.post("/{video_id}/failed", response_model=VideoRead)
def mark_video_failed(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """前端在上传失败时调用，将视频记录标记为 failed。"""
    video = db.query(Video).filter(Video.id == video_id, Video.owner_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video.status = "failed"
    db.add(video)
    db.commit()
    db.refresh(video)
    return video
