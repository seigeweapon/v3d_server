import io
import json
import zipfile
from datetime import datetime
from typing import List
from urllib.request import urlopen
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.api import deps
from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.video import (
    VideoCreate,
    VideoRead,
    VideoUpload,
    VideoUpdate,
    VideoDownloadRequest,
    VideoDownloadResponse,
    FileDownloadInfo,
    VideoVisibilityUpdate,
)
from app.utils.storage import (
    generate_tos_post_form_data,
    delete_tos_objects_by_prefix,
    list_tos_objects,
    generate_tos_download_url,
)
from app.utils.video_metadata import get_video_metadata_from_file

router = APIRouter(prefix="/videos", tags=["videos"])


def parse_visible_user_ids(visible_to_user_ids: str) -> List[int]:
    """解析 visible_to_user_ids JSON 字符串为整数列表"""
    if not visible_to_user_ids:
        return []
    try:
        return json.loads(visible_to_user_ids)
    except (json.JSONDecodeError, TypeError):
        return []


def can_user_view_video(video: Video, user: User) -> bool:
    """检查用户是否有权限查看视频"""
    # 管理员可以看到所有视频
    if user.is_superuser:
        return True
    
    # 所有者总是可以看到自己的视频
    if video.owner_id == user.id:
        return True
    
    # 检查是否是公开的视频
    if video.is_public:
        return True
    
    # 检查管理员授权的用户列表
    if video.visible_to_user_ids:
        visible_ids = parse_visible_user_ids(video.visible_to_user_ids)
        if user.id in visible_ids:
            return True
    
    return False


@router.get("/", response_model=List[VideoRead])
def list_videos(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)
):
    """列出用户有权限查看的视频"""
    query = db.query(Video).options(joinedload(Video.owner))
    
    # 管理员可以看到所有视频
    if current_user.is_superuser:
        videos = query.all()
    else:
        # 普通用户只能看到：自己的视频、公开的视频、或管理员授权的视频
        # 由于 SQLite 不支持 JSON 查询，我们需要先获取所有可能的数据，然后在 Python 中过滤
        # 或者使用更简单的 SQL 查询：owner_id == current_user.id OR is_public == True
        # 对于 visible_to_user_ids，我们先用 SQL 过滤掉明显不符合的，然后在 Python 中检查 JSON
        
        # 先获取可能可见的视频：自己的或公开的
        potential_videos = query.filter(
            or_(
                Video.owner_id == current_user.id,
                Video.is_public == True,
                Video.visible_to_user_ids.isnot(None)  # 可能有管理员授权的
            )
        ).all()
        
        # 在 Python 中过滤出真正可见的视频
        videos = [v for v in potential_videos if can_user_view_video(v, current_user)]
    
    return videos


@router.post("/upload", response_model=VideoRead)
def upload_video(
    video_in: VideoUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """创建视频记录并生成 TOS 上传表单数据"""
    # 生成 UUID 作为目录名
    uuid_dir = str(uuid4())
    
    # 生成 TOS 路径前缀：<tos_key_prefix>/<uuid>（用于数据库存储）
    # 注意：uuid 层级之下会有多个文件夹：video、background、calibration
    key_prefix = settings.tos_key_prefix.rstrip("/")
    uuid_path = f"{key_prefix}/{uuid_dir}"
    
    # 用于写入数据库/展示的 tos_path，可包含 bucket 信息（只到 UUID 目录）
    tos_path = f"tos://{settings.tos_bucket}/{uuid_path}/"
    
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
    # 加载owner关系以便在schema中获取full_name
    db.refresh(video, ['owner'])
    
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
        object_key = f"{key_prefix}/{uuid_dir}/placeholder"
        post_form_data = generate_tos_post_form_data(object_key)
        post_form_data_list.append(post_form_data)
    
    # 返回视频记录和上传表单数据
    video_read = VideoRead.from_orm(video)
    video_read.post_form_data_list = post_form_data_list
    return video_read


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
    # 加载owner关系以便在schema中获取full_name
    db.refresh(video, ['owner'])
    return VideoRead.from_orm(video)


@router.get("/{video_id}", response_model=VideoRead)
def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取视频详情（需要权限检查）"""
    video = db.query(Video).options(joinedload(Video.owner)).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 检查权限
    if not can_user_view_video(video, current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to view this video")
    
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
    只有管理员可以删除视频。
    """
    # 检查权限：只有管理员可以删除
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以删除视频")
    
    # 管理员可以删除任何视频，普通用户只能删除自己的
    if current_user.is_superuser:
        video = db.query(Video).filter(Video.id == video_id).first()
    else:
        video = db.query(Video).filter(Video.id == video_id, Video.owner_id == current_user.id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 从 tos_path 中提取路径前缀（去掉 tos://bucket/ 前缀）
    # tos_path 格式: tos://{bucket}/{prefix}/{uuid}/
    tos_path = video.tos_path
    if tos_path.startswith("tos://"):
        path_without_schema = tos_path[6:]  # 去掉 "tos://"
        # 提取 bucket 后面的路径
        if "/" in path_without_schema:
            bucket, path_after_bucket = path_without_schema.split("/", 1)
            uuid_path = path_after_bucket.rstrip("/")
        else:
            raise HTTPException(status_code=400, detail="Invalid tos_path format")
    else:
        uuid_path = tos_path.rstrip("/")
    
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
    video = db.query(Video).options(joinedload(Video.owner)).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 只有所有者可以标记视频为 ready
    if video.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can mark video as ready")

    # TODO: 未来可以在这里对 TOS 做一次 HEAD Object 校验，确认对象存在
    video.status = "ready"
    db.add(video)
    db.commit()
    db.refresh(video)
    # 加载owner关系以便在schema中获取full_name
    db.refresh(video, ['owner'])
    return video


@router.post("/{video_id}/failed", response_model=VideoRead)
def mark_video_failed(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """前端在上传失败时调用，将视频记录标记为 failed。"""
    video = db.query(Video).options(joinedload(Video.owner)).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 只有所有者可以标记视频为 failed
    if video.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can mark video as failed")

    video.status = "failed"
    db.add(video)
    db.commit()
    db.refresh(video)
    # 加载owner关系以便在schema中获取full_name
    db.refresh(video, ['owner'])
    return video


@router.patch("/{video_id}", response_model=VideoRead)
def update_video(
    video_id: int,
    video_update: VideoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """更新视频的基本信息（摄影棚、制片方、制作、动作）"""
    video = db.query(Video).options(joinedload(Video.owner)).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 只有所有者可以更新视频信息
    if video.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the owner can update video")

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
    # 加载owner关系以便在schema中获取full_name
    db.refresh(video, ['owner'])
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


@router.post("/{video_id}/download-zip")
def download_video_zip(
    video_id: int,
    download_request: VideoDownloadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    将选定类型的所有文件打包为 ZIP 并返回（流式响应）。
    ZIP 内部目录格式: v3d_data_YYYYMMDD_hhmmss/<file_type>/<filename>
    """
    video = db.query(Video).options(joinedload(Video.owner)).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 检查权限：只有可见的视频才能下载
    if not can_user_view_video(video, current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to download this video")
    
    # 提取 UUID 目录路径
    tos_path = video.tos_path
    if tos_path.startswith("tos://"):
        path_without_schema = tos_path[6:]
        if "/" in path_without_schema:
            _, path_after_bucket = path_without_schema.split("/", 1)
            uuid_path = path_after_bucket.rstrip("/")
        else:
            raise HTTPException(status_code=400, detail="Invalid tos_path format")
    else:
        uuid_path = tos_path.rstrip("/")
    
    valid_file_types = {"video", "background", "calibration"}
    requested_types = set(download_request.file_types)
    invalid_types = requested_types - valid_file_types
    if invalid_types:
        raise HTTPException(status_code=400, detail=f"Invalid file types: {invalid_types}")
    
    # 收集需要打包的对象
    files_to_zip: list[FileDownloadInfo] = []
    for file_type in download_request.file_types:
        type_prefix = f"{uuid_path}/{file_type}/"
        try:
            object_keys = list_tos_objects(type_prefix)
            for object_key in object_keys:
                filename = object_key.split("/")[-1]
                download_url = generate_tos_download_url(object_key)
                files_to_zip.append(
                    FileDownloadInfo(
                        object_key=object_key,
                        download_url=download_url,
                        filename=filename,
                        file_type=file_type,
                    )
                )
        except Exception as e:
            import logging
            logging.warning(f"列出文件类型 {file_type} 失败 (前缀: {type_prefix}): {e}")
            continue
    
    if not files_to_zip:
        raise HTTPException(status_code=404, detail="No files found for the specified file types")
    
    # 生成 ZIP 文件名和内部根目录名
    ts_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    zip_root = f"v3d_data_{ts_str}"
    zip_filename = f"{zip_root}.zip"
    
    def zip_generator():
        with io.BytesIO() as mem_buf:
            with zipfile.ZipFile(mem_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for idx, file_info in enumerate(files_to_zip, start=1):
                    arcname = f"{zip_root}/{file_info.file_type}/{file_info.filename}"
                    try:
                        with urlopen(file_info.download_url) as resp:
                            content = resp.read()
                        zf.writestr(arcname, content)
                    except Exception as e:
                        import logging
                        logging.error(f"打包文件失败: {file_info.object_key}, 错误: {e}")
                        continue
            mem_buf.seek(0)
            chunk = mem_buf.read(8192)
            while chunk:
                yield chunk
                chunk = mem_buf.read(8192)
    
    headers = {
        "Content-Disposition": f'attachment; filename="{zip_filename}"'
    }
    return StreamingResponse(zip_generator(), media_type="application/zip", headers=headers)


@router.patch("/{video_id}/visibility", response_model=VideoRead)
def update_video_visibility(
    video_id: int,
    visibility_update: VideoVisibilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """更新视频的可见性设置"""
    video = db.query(Video).options(joinedload(Video.owner)).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 所有者可以修改 is_public，管理员可以修改所有可见性属性
    if video.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only the owner or admin can update visibility")
    
    # 所有者只能修改 is_public
    if video.owner_id == current_user.id and not current_user.is_superuser:
        if visibility_update.visible_to_user_ids is not None:
            raise HTTPException(status_code=403, detail="Only admin can set visible_to_user_ids")
        if visibility_update.is_public is not None:
            video.is_public = visibility_update.is_public
    else:
        # 管理员可以修改所有属性
        if visibility_update.is_public is not None:
            video.is_public = visibility_update.is_public
        if visibility_update.visible_to_user_ids is not None:
            # 将列表转换为 JSON 字符串
            if visibility_update.visible_to_user_ids:
                video.visible_to_user_ids = json.dumps(visibility_update.visible_to_user_ids)
            else:
                video.visible_to_user_ids = None
    
    db.add(video)
    db.commit()
    db.refresh(video)
    return video
