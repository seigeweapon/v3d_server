from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.database import get_db
from app.models.user import User
from app.models.calibration import Calibration
from app.schemas.calibration import CalibrationCreate, CalibrationRead

router = APIRouter(prefix="/calibrations", tags=["calibrations"])


@router.get("/", response_model=List[CalibrationRead])
def list_calibrations(
    db: Session = Depends(get_db), current_user: User = Depends(deps.get_current_active_user)
):
    return db.query(Calibration).filter(Calibration.owner_id == current_user.id).all()


@router.post("/", response_model=CalibrationRead)
def create_calibration(
    calibration_in: CalibrationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    calibration = Calibration(
        owner_id=current_user.id,
        **calibration_in.dict()
    )
    db.add(calibration)
    db.commit()
    db.refresh(calibration)
    return calibration


@router.get("/{calibration_id}", response_model=CalibrationRead)
def get_calibration(
    calibration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    calibration = db.query(Calibration).filter(
        Calibration.id == calibration_id,
        Calibration.owner_id == current_user.id
    ).first()
    if not calibration:
        raise HTTPException(status_code=404, detail="Calibration not found")
    return calibration


@router.delete("/{calibration_id}")
def delete_calibration(
    calibration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    calibration = db.query(Calibration).filter(
        Calibration.id == calibration_id,
        Calibration.owner_id == current_user.id
    ).first()
    if not calibration:
        raise HTTPException(status_code=404, detail="Calibration not found")
    db.delete(calibration)
    db.commit()
    return {"ok": True}

