from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.database import get_db
from app.models.job import Job
from app.models.user import User

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{job_id}")
def download_result(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == current_user.id).first()
    if not job or not job.result_path:
        raise HTTPException(status_code=404, detail="Result not available")
    return FileResponse(path=job.result_path, filename=f"result-{job_id}.zip")
