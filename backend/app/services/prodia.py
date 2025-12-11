"""
Thin client for Prodia workflow_execution APIs.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any, Dict, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class ProdiaClientError(RuntimeError):
    """Raised when Prodia API responds with an error or unexpected payload."""


class ProdiaClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        env: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.prodia_base_url).rstrip("/")
        self.api_key = api_key or settings.prodia_api_key
        self.env = env or settings.prodia_env

    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise ProdiaClientError("Prodia API key is not configured")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        if self.env:
            headers["x-tt-env"] = self.env
        return headers

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=30)
        if not resp.ok:
            logger.error("Prodia request failed: %s %s -> %s %s", path, payload, resp.status_code, resp.text)
            raise ProdiaClientError(f"Prodia request failed with status {resp.status_code}")
        try:
            return resp.json()
        except json.JSONDecodeError as exc:
            raise ProdiaClientError("Prodia response is not valid JSON") from exc

    @staticmethod
    def _is_base64(s: str) -> bool:
        """检查字符串是否为有效的base64编码。"""
        try:
            base64.b64decode(s)
            return True
        except Exception:
            return False

    @staticmethod
    def _ensure_base64_blob(raw: str | Dict[str, Any]) -> str:
        """Accept either a pre-encoded base64 string or dict and produce base64 string."""
        if isinstance(raw, str):
            # If looks like base64, just return; otherwise encode.
            if ProdiaClient._is_base64(raw):
                return raw
            return base64.b64encode(raw.encode()).decode()
        data = json.dumps(raw)
        return base64.b64encode(data.encode()).decode()

    def start_workflow(self, blob: str | Dict[str, Any]) -> str:
        """Start workflow and return runId."""
        payload: Dict[str, Any] = {
            "workflowName": settings.prodia_workflow_name,
            "workflowDpName": settings.prodia_workflow_dp_name,
            # 如果blob已经是base64字符串，直接使用；否则进行编码
            "input": {"blobs": [blob if isinstance(blob, str) and self._is_base64(blob) else self._ensure_base64_blob(blob)]},
            "timeout": settings.prodia_timeout_seconds,
            "callbackUri": settings.prodia_callback_uri or "",
            "callbackArgs": settings.prodia_callback_args or "",
            "taskList": settings.prodia_task_list,
            "priority": settings.prodia_priority,
        }
        data = self._post("/prodia/v1/workflow_execution/start", payload)
        run_id = data.get("runId")
        if not run_id:
            logger.error("Prodia start response missing runId: %s", data)
            raise ProdiaClientError("Prodia start did not return runId")
        return run_id

    def terminate_workflow(self, run_id: str) -> Dict[str, Any]:
        payload = {"runId": run_id}
        return self._post("/prodia/v1/workflow_execution/terminate", payload)

    def get_workflow_status(self, run_id: str) -> Dict[str, Any]:
        payload = {"runId": run_id}
        return self._post("/prodia/v1/workflow_execution/get", payload)

    @staticmethod
    def extract_status(response_data: Dict[str, Any]) -> Optional[str]:
        """
        Try to pull a status field from different possible shapes.
        """
        for key in ("status", "state"):
            if key in response_data:
                return response_data.get(key)
        workflow_execution = response_data.get("workflowExecution") or {}
        for key in ("status", "state"):
            if key in workflow_execution:
                return workflow_execution.get(key)
        return None


client = ProdiaClient()

