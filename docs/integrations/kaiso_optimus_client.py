"""Cliente de referência Kaiso -> Optimus (v1).

Uso esperado:
- OPTIMUS_API_URL
- OPTIMUS_API_KEY
- OPTIMUS_PROJECT_ID
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}


@dataclass(slots=True)
class OptimusConfig:
    api_url: str
    api_key: str
    project_id: str
    timeout_seconds: float = 5.0
    max_attempts: int = 3

    @staticmethod
    def from_env() -> "OptimusConfig":
        return OptimusConfig(
            api_url=os.environ["OPTIMUS_API_URL"].rstrip("/"),
            api_key=os.environ["OPTIMUS_API_KEY"],
            project_id=os.environ["OPTIMUS_PROJECT_ID"],
        )


class OptimusIntegrationError(RuntimeError):
    pass


class OptimusClient:
    def __init__(self, config: OptimusConfig) -> None:
        self._config = config

    def run_engineering_scenario(
        self,
        *,
        scenario_id: str,
        objective: str,
        stack: str,
        files: list[dict[str, str]],
        request_id: str,
        observed_error: str | None = None,
        additional_instructions: str | None = None,
        diff_text: str | None = None,
        plan_id: str | None = None,
    ) -> dict:
        payload: dict[str, object] = {
            "project_id": self._config.project_id,
            "scenario_id": scenario_id,
            "objective": objective,
            "inputs": {
                "stack": stack,
                "objective": objective,
                "files": files,
            },
        }
        if observed_error is not None:
            payload["inputs"]["observed_error"] = observed_error
        if additional_instructions is not None:
            payload["inputs"]["additional_instructions"] = additional_instructions
        if diff_text is not None:
            payload["inputs"]["diff_text"] = diff_text
        if plan_id is not None:
            payload["plan_id"] = plan_id
        return self._post_with_retry("/scenarios/run", payload=payload, request_id=request_id)

    def _post_with_retry(self, path: str, payload: dict[str, object], request_id: str) -> dict:
        url = f"{self._config.api_url}{path}"
        body = json.dumps(payload).encode("utf-8")

        attempt = 0
        while True:
            attempt += 1
            req = urllib.request.Request(
                url=url,
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self._config.api_key}",
                    "Content-Type": "application/json",
                    "X-Request-Id": request_id,
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=self._config.timeout_seconds) as resp:
                    raw = resp.read().decode("utf-8")
                    return json.loads(raw)
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read().decode("utf-8") if exc.fp else ""
                if status in TRANSIENT_STATUS_CODES and attempt < self._config.max_attempts:
                    time.sleep(0.2 * attempt)
                    continue
                raise OptimusIntegrationError(f"Optimus HTTP {status}: {raw}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt < self._config.max_attempts:
                    time.sleep(0.2 * attempt)
                    continue
                raise OptimusIntegrationError(f"Optimus network/timeout error: {exc}") from exc
