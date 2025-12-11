"""Prodia workflow integration helpers."""

from __future__ import annotations

import base64
import json
import logging
import os
from typing import Dict

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.job import Job
from app.models.video import Video
from app.services.prodia import ProdiaClientError, client
from app.services.v3d_train_wf.v3d_train_workflow_pb2 import V3DTrainWorkflowRequest

logger = logging.getLogger(__name__)


def _build_blob(job: Job, video: Video) -> str:
    """Compose a best-effort payload for the upstream workflow according to protobuf definition."""
    # Parse user-provided parameters from JSON string
    user_params = {}
    if job.parameters:
        try:
            user_params = json.loads(job.parameters)
        except Exception as e:
            logger.error(f"Failed to parse job parameters: {e}")
    
    # 根据v3d_wf_start.py的实现构建V3DTrainWorkflowRequest
    req = V3DTrainWorkflowRequest(
        tos=V3DTrainWorkflowRequest.V3dTosInfo(
            ak=settings.tos_access_key,
            sk=settings.tos_secret_key,
            endpoint=settings.tos_endpoint,
            region=settings.tos_region
        ),
        workspace_url=video.tos_path,
        output_url=job.tos_path,
        # 从用户参数中获取其他可选字段
        gop_size=user_params.get("gop_size", 100),
        frame_start=user_params.get("frame_start", 0),
        frame_number=user_params.get("frame_number", 0),
        camera_number=user_params.get("camera_number", 0),
        matting_mode=user_params.get("matting_mode", "bg_matting"),
        training_configs=json.dumps(user_params.get("training_configs", {})) if isinstance(user_params.get("training_configs"), dict) else user_params.get("training_configs", "{}"),
        do_devignetting=user_params.get("do_devignetting", False),
        debug=user_params.get("debug", False),
        op_versions=json.dumps(user_params.get("op_versions", {})) if isinstance(user_params.get("op_versions"), dict) else user_params.get("op_versions", "{}"),
        render_views_url=user_params.get("render_views_url", "")
    )
    
    # 序列化并编码为base64
    input_blob = base64.b64encode(req.SerializeToString()).decode()
    
    return input_blob


def submit_processing_job(db: Session, job: Job, video: Video) -> str:
    """
    Start a workflow run and persist run_id + status onto the job.
    """
    blob = _build_blob(job, video)
    try:
        # 直接传递已经编码好的base64字符串
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
