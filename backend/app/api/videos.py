from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.database import get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoCreate, VideoRead

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/", response_model=List[VideoRead])
def list_videos(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)
):
    return db.query(Video).filter(Video.owner_id == current_user.id).all()


@router.post("/", response_model=VideoRead)
def create_video(
    video_in: VideoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    # Verify background_id and calibration_id exist and belong to user
    from app.models.background import Background
    from app.models.calibration import Calibration
    
    background = db.query(Background).filter(
        Background.id == video_in.background_id,
        Background.owner_id == current_user.id
    ).first()
    if not background:
        raise HTTPException(status_code=404, detail="Background not found")
    
    calibration = db.query(Calibration).filter(
        Calibration.id == video_in.calibration_id,
        Calibration.owner_id == current_user.id
    ).first()
    if not calibration:
        raise HTTPException(status_code=404, detail="Calibration not found")
    
    video = Video(
        owner_id=current_user.id,
        **video_in.dict()
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


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
    video = db.query(Video).filter(Video.id == video_id, Video.owner_id == current_user.id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    db.delete(video)
    db.commit()
    return {"ok": True}
