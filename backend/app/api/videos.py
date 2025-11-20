from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.database import get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoRead
from app.utils.storage import save_file

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/", response_model=List[VideoRead])
def list_videos(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)
):
    return db.query(Video).filter(Video.owner_id == current_user.id).all()


@router.post("/upload", response_model=VideoRead)
def upload_video(
    file: UploadFile = File(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    storage_path = save_file(file.filename, file.file)
    video = Video(
        owner_id=current_user.id,
        filename=file.filename,
        storage_path=storage_path,
        description=description,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.delete("/{video_id}")
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    video = db.query(Video).filter(Video.id == video_id, Video.owner_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    db.delete(video)
    db.commit()
    return {"ok": True}
