from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(deps.get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserRead)
def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.password:
        raise HTTPException(status_code=400, detail="Password change not implemented")
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
