"""Prodia workflow integration helpers."""

from __future__ import annotations

import json
import logging
from typing import Dict

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.video import Video
from app.services.prodia import ProdiaClientError, client

logger = logging.getLogger(__name__)


def _build_blob(job: Job, video: Video) -> str:
    """Compose a best-effort payload for the upstream workflow."""
    payload: Dict[str, object] = {
        "job_id": job.id,
        "video_tos_path": video.tos_path,
    }
    if job.parameters:
        try:
            payload.update(json.loads(job.parameters))
        except Exception:
            payload["parameters_raw"] = job.parameters
    return json.dumps(payload)


def submit_processing_job(db: Session, job: Job, video: Video) -> str:
    """
    Start a workflow run and persist run_id + status onto the job.
    """
    blob = _build_blob(job, video)
    try:
        run_id = client.start_workflow(blob)
        job.run_id = run_id
        job.status = "processing"
        db.add(job)
        db.commit()
        db.refresh(job, ["owner"])
        return run_id
    except ProdiaClientError:
        logger.exception("Failed to start workflow for job %s", job.id)
        job.status = "failed"
        db.add(job)
        db.commit()
        raise


def terminate_processing_job(db: Session, job: Job) -> Dict[str, str]:
    if not job.run_id:
        raise ProdiaClientError("Job has no run_id; cannot terminate upstream workflow")
    try:
        resp = client.terminate_workflow(job.run_id)
        job.status = "terminated"
        db.add(job)
        db.commit()
        db.refresh(job, ["owner"])
        return {"status": job.status, "run_id": job.run_id, "response": resp}
    except ProdiaClientError:
        logger.exception("Failed to terminate workflow for job %s", job.id)
        raise


def sync_processing_status(db: Session, job: Job) -> Dict[str, str | None]:
    if not job.run_id:
        raise ProdiaClientError("Job has no run_id; cannot query upstream workflow")
    resp = client.get_workflow_status(job.run_id)
    status = client.extract_status(resp) or job.status
    job.status = status
    db.add(job)
    db.commit()
    db.refresh(job, ["owner"])
    return {"status": job.status, "run_id": job.run_id, "raw": resp}
