"""Placeholder integrations for the external processing pipeline.

Replace these stubs with the actual task dispatching/monitoring logic from the
existing processing service when performing the real integration.
"""

from typing import Dict


def submit_processing_job(job_id: int, video_path: str, parameters: str | None = None) -> Dict[str, str]:
    # TODO: Plug into real processing service.
    return {"job_id": job_id, "status": "submitted"}


def get_processing_status(job_id: int) -> Dict[str, str]:
    # TODO: Replace with real status lookup.
    return {"job_id": job_id, "status": "pending"}
