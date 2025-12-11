from typing import List
from uuid import uuid4
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.database import get_db
from app.models.job import Job
from app.models.video import Video
from app.models.user import User
from app.schemas.job import JobCreate, JobRead, JobUpdate
from app.services import tasks
from app.utils.storage import delete_tos_objects_by_prefix

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=List[JobRead])
def list_jobs(db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)):
    return db.query(Job).filter(Job.owner_id == current_user.id).all()


@router.post("/", response_model=JobRead)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    video = db.query(Video).filter(Video.id == job_in.video_id, Video.owner_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

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

    tasks.submit_processing_job(job.id, video.tos_path, job.parameters)

    return job


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    删除任务记录，如果任务有tos_path，则同时删除TOS上的相关文件。
    """
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
    return job
