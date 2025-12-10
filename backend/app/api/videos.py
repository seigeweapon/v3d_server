from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoCreate, VideoRead, VideoUpload, VideoUpdate
from app.utils.storage import generate_tos_post_form_data, delete_tos_objects_by_prefix
from app.utils.video_metadata import get_video_metadata_from_file

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
    
    # 计算相机数：如果提供了 camera_count 则使用，否则从 file_infos 中统计视频文件数量
    if video_in.camera_count is not None:
        camera_count = video_in.camera_count
    elif video_in.file_infos:
        # 统计以 cam_ 开头且扩展名为 mp4 或 ts 的文件数量
        camera_count = sum(
            1 for file_info in video_in.file_infos
            if file_info.get("name", "").startswith("cam_") and 
               (file_info.get("name", "").endswith(".mp4") or file_info.get("name", "").endswith(".ts"))
        )
        if camera_count == 0:
            camera_count = 1  # 如果没有找到视频文件，默认值为1
    else:
        camera_count = 1  # 默认值
    
    # 使用前端传来的元数据，如果没有提供则使用默认值
    prime_camera_number = video_in.prime_camera_number if video_in.prime_camera_number is not None else 1
    frame_count = video_in.frame_count if video_in.frame_count is not None else 0
    frame_rate = video_in.frame_rate if video_in.frame_rate is not None else 30.0
    frame_width = video_in.frame_width if video_in.frame_width is not None else 1920
    frame_height = video_in.frame_height if video_in.frame_height is not None else 1080
    video_format = video_in.video_format if video_in.video_format is not None else "mp4"
    
    # 创建视频记录
    video = Video(
        owner_id=current_user.id,
        studio=video_in.studio,
        producer=video_in.producer,
        production=video_in.production,
        action=video_in.action,
        camera_count=camera_count,  # 使用计算出的相机数
        prime_camera_number=prime_camera_number,
        frame_count=frame_count,
        frame_rate=frame_rate,
        frame_width=frame_width,
        frame_height=frame_height,
        video_format=video_format,
        tos_path=tos_path,
        status="uploading",  # 初始状态为上传中
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    
    # 为每个文件生成 PostObject 表单数据
    # 文件顺序：所有视频文件（cam_*.mp4/ts），所有背景文件（cam_*.png/jpg），标定文件（calibration_ba.json）
    post_form_data_list = []
    if video_in.file_infos:
        key_prefix = settings.tos_key_prefix.rstrip("/")
        
        for file_info in video_in.file_infos:
            filename = file_info.get("name", "unknown")
            content_type = file_info.get("type")  # MIME 类型
            
            # 根据文件名判断文件类型
            if filename.startswith("cam_") and (filename.endswith(".mp4") or filename.endswith(".ts")):
                category = "video"
            elif filename.startswith("cam_") and (filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".jpeg")):
                category = "background"
            elif filename.startswith("calibration_"):
                category = "calibration"
            else:
                # 默认根据 MIME 类型判断
                if content_type and content_type.startswith("video/"):
                    category = "video"
                elif content_type and content_type.startswith("image/"):
                    category = "background"
                else:
                    category = "calibration"
            
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


@router.patch("/{video_id}", response_model=VideoRead)
def update_video(
    video_id: int,
    video_update: VideoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """更新视频的基本信息（摄影棚、制片方、制作、动作）"""
    video = db.query(Video).filter(Video.id == video_id, Video.owner_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # 只更新提供的字段
    if video_update.studio is not None:
        video.studio = video_update.studio
    if video_update.producer is not None:
        video.producer = video_update.producer
    if video_update.production is not None:
        video.production = video_update.production
    if video_update.action is not None:
        video.action = video_update.action

    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.post("/extract-metadata")
async def extract_video_metadata(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    从视频文件中提取元数据（支持HEVC等格式）
    使用 ffprobe 读取视频信息
    """
    # 检查文件类型
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="文件必须是视频格式")
    
    try:
        # 读取文件内容
        file_data = await file.read()
        
        # 使用 ffprobe 读取元数据
        metadata = get_video_metadata_from_file(file_data, file.filename or 'video.mp4')
        
        return {
            "duration": metadata['duration'],
            "width": metadata['width'],
            "height": metadata['height'],
            "frame_rate": metadata['frame_rate'],
            "frame_count": metadata['frame_count'],
            "format": metadata['format'],
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"读取视频元数据失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理视频文件失败: {str(e)}")
