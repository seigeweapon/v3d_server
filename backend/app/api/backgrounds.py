from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.database import get_db
from app.models.user import User
from app.models.background import Background
from app.schemas.background import BackgroundCreate, BackgroundRead

router = APIRouter(prefix="/backgrounds", tags=["backgrounds"])


@router.get("/", response_model=List[BackgroundRead])
def list_backgrounds(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)
):
    return db.query(Background).filter(Background.owner_id == current_user.id).all()


@router.post("/", response_model=BackgroundRead)
def create_background(
    background_in: BackgroundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    background = Background(
        owner_id=current_user.id,
        **background_in.dict()
    )
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

