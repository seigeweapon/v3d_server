from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.database import get_db
from app.models.job import Job
from app.models.video import Video
from app.models.user import User
from app.schemas.job import JobCreate, JobRead
from app.services import tasks

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

    job = Job(
        video_id=job_in.video_id,
        owner_id=current_user.id,
        parameters=job_in.parameters,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    tasks.submit_processing_job(job.id, video.storage_path, job.parameters)

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
