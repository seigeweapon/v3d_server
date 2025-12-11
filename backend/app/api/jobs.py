from typing import List
from uuid import uuid4
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.api import deps
from app.core.config import settings
from app.database import get_db
from app.models.job import Job
from app.models.video import Video
from app.models.user import User
from app.schemas.job import JobCreate, JobRead, JobUpdate, JobVisibilityUpdate
from app.services import tasks
from app.services.prodia import ProdiaClientError
from app.utils.storage import delete_tos_objects_by_prefix

router = APIRouter(prefix="/jobs", tags=["jobs"])


def parse_visible_user_ids(visible_to_user_ids: str) -> List[int]:
    """解析 visible_to_user_ids JSON 字符串为整数列表"""
    if not visible_to_user_ids:
        return []
    try:
        return json.loads(visible_to_user_ids)
    except (json.JSONDecodeError, TypeError):
        return []


def can_user_view_job(job: Job, user: User) -> bool:
    """检查用户是否有权限查看任务"""
    # 管理员可以看到所有任务
    if user.is_superuser:
        return True
    
    # 所有者总是可以看到自己的任务
    if job.owner_id == user.id:
        return True
    
    # 检查是否是公开的任务
    if job.is_public:
        return True
    
    # 检查管理员授权的用户列表
    if job.visible_to_user_ids:
        visible_ids = parse_visible_user_ids(job.visible_to_user_ids)
        if user.id in visible_ids:
            return True
    
    return False


@router.get("/", response_model=List[JobRead])
def list_jobs(db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)):
    """列出用户有权限查看的任务"""
    query = db.query(Job).options(joinedload(Job.owner))
    
    # 管理员可以看到所有任务
    if current_user.is_superuser:
        jobs = query.all()
    else:
        # 普通用户只能看到：自己的任务、公开的任务、或管理员授权的任务
        potential_jobs = query.filter(
            or_(
                Job.owner_id == current_user.id,
                Job.is_public == True,
                Job.visible_to_user_ids.isnot(None)  # 可能有管理员授权的
            )
        ).all()
        
        # 在 Python 中过滤出真正可见的任务
        jobs = [j for j in potential_jobs if can_user_view_job(j, current_user)]
    
    return jobs


@router.post("/", response_model=JobRead)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    # 检查视频是否存在以及用户是否有权限使用该视频创建任务
    video = db.query(Video).filter(Video.id == job_in.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 管理员可以为任何视频创建任务，普通用户只能为可见的视频创建任务
    if not current_user.is_superuser:
        # 导入 can_user_view_video 函数（从 videos.py）
        from app.api.videos import can_user_view_video
        if not can_user_view_video(video, current_user):
            raise HTTPException(status_code=403, detail="You don't have permission to create job with this video")

    # 生成 UUID 作为目录名
    uuid_dir = str(uuid4())
    
    # 生成 TOS 路径：tos://<bucket>/<TOS_JOB_KEY_PREFIX>/<uuid>/
    job_key_prefix = settings.tos_job_key_prefix.rstrip("/")
    tos_path = f"tos://{settings.tos_bucket}/{job_key_prefix}/{uuid_dir}/"

    job = Job(
        video_id=job_in.video_id,
        owner_id=current_user.id,
        parameters=job_in.parameters,
        notes=job_in.notes,
        status="pending",
        tos_path=tos_path,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    # 加载owner关系以便在schema中获取full_name
    db.refresh(job, ["owner"])

    try:
        tasks.submit_processing_job(db, job, video)
    except ProdiaClientError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to start upstream workflow: {exc}") from exc

    return job


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """获取任务详情（需要权限检查）"""
    job = db.query(Job).options(joinedload(Job.owner)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 检查权限
    if not can_user_view_job(job, current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to view this job")
    
    return job


@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    删除任务记录，如果任务有tos_path，则同时删除TOS上的相关文件。
    只有管理员可以删除任务。
    """
    # 检查权限：只有管理员可以删除
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以删除任务")
    
    # 管理员可以删除任何任务，普通用户只能删除自己的
    if current_user.is_superuser:
        job = db.query(Job).filter(Job.id == job_id).first()
    else:
        job = db.query(Job).filter(Job.id == job_id, Job.owner_id == current_user.id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 如果任务有tos_path，删除TOS上的文件
    if job.tos_path:
        # 从 tos_path 中提取路径前缀（去掉 tos://bucket/ 前缀）
        # tos_path 格式: tos://{bucket}/{prefix}/{uuid}/
        tos_path = job.tos_path
        if tos_path.startswith("tos://"):
            path_without_schema = tos_path[6:]  # 去掉 "tos://"
            # 提取 bucket 后面的路径
            if "/" in path_without_schema:
                _, path_after_bucket = path_without_schema.split("/", 1)
                # 路径格式：<tos_job_key_prefix>/<uuid>/
                prefix = path_after_bucket.rstrip("/") + "/"
            else:
                raise HTTPException(status_code=400, detail="Invalid tos_path format")
        else:
            prefix = tos_path.rstrip("/") + "/"
        
        # 删除 TOS 上的所有文件
        try:
            delete_tos_objects_by_prefix(prefix)
        except RuntimeError as e:
            logging.error(f"删除 TOS 文件失败 (prefix={prefix}): {e}")
            raise HTTPException(
                status_code=500,
                detail=f"删除 TOS 文件失败: {str(e)}。数据库记录未删除，请稍后重试。"
            )
    
    # 删除数据库记录
    try:
        db.delete(job)
        db.commit()
    except Exception as e:
        logging.error(f"删除数据库记录失败 (job_id={job_id}): {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"删除数据库记录失败: {str(e)}"
        )
    
    return {"ok": True}


@router.patch("/{job_id}", response_model=JobRead)
def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """更新任务的备注"""
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 只更新提供的字段
    if job_update.notes is not None:
        job.notes = job_update.notes

    db.add(job)
    db.commit()
    db.refresh(job)
    # 加载owner关系以便在schema中获取full_name
    db.refresh(job, ['owner'])
    return job


@router.patch("/{job_id}/visibility", response_model=JobRead)
def update_job_visibility(
    job_id: int,
    visibility_update: JobVisibilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """更新任务的可见性设置"""
    job = db.query(Job).options(joinedload(Job.owner)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 所有者可以修改 is_public，管理员可以修改所有可见性属性
    if job.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only the owner or admin can update visibility")
    
    # 所有者只能修改 is_public
    if job.owner_id == current_user.id and not current_user.is_superuser:
        if visibility_update.visible_to_user_ids is not None:
            raise HTTPException(status_code=403, detail="Only admin can set visible_to_user_ids")
        if visibility_update.is_public is not None:
            job.is_public = visibility_update.is_public
    else:
        # 管理员可以修改所有属性
        if visibility_update.is_public is not None:
            job.is_public = visibility_update.is_public
        if visibility_update.visible_to_user_ids is not None:
            # 将列表转换为 JSON 字符串
            if visibility_update.visible_to_user_ids:
                job.visible_to_user_ids = json.dumps(visibility_update.visible_to_user_ids)
            else:
                job.visible_to_user_ids = None
    
    db.add(job)
    db.commit()
    db.refresh(job)
    db.refresh(job, ['owner'])
    return job


@router.post("/{job_id}/terminate", response_model=JobRead)
def terminate_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    job = db.query(Job).options(joinedload(Job.owner)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only owner or admin can terminate job")
    try:
        tasks.terminate_processing_job(db, job)
    except ProdiaClientError as exc:
        raise HTTPException(status_code=502, detail=f"Terminate upstream failed: {exc}") from exc
    return job


@router.post("/{job_id}/sync-status", response_model=JobRead)
def sync_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    job = db.query(Job).options(joinedload(Job.owner)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not can_user_view_job(job, current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to sync this job")
    try:
        tasks.sync_processing_status(db, job)
    except ProdiaClientError as exc:
        raise HTTPException(status_code=502, detail=f"Sync upstream status failed: {exc}") from exc
    return job
