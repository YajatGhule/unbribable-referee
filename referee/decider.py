"""Minimal client for a running Strands Decider server (POST /v1/systemone).

Start one with:
    strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8099

Shape follows the client in strands-labs/strands-decider/examples/strands (Apache-2.0):
stdlib only, synchronous, one state with many questions per round trip, so the state is
encoded once and shared across every question.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Mapping

DEFAULT_URL = os.environ.get("STRANDS_DECIDER_URL", "http://127.0.0.1:8099")
SERVE_HINT = "strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8099"


class DeciderUnavailable(RuntimeError):
    pass


def noul(instructions: str, true: str | None = None, false: str | None = None) -> dict[str, Any]:
    """Yes/no question. The answer is P(true)."""
    q: dict[str, Any] = {"type": "noul", "instructions": instructions}
    criteria = {k: v for k, v in (("true", true), ("false", false)) if v}
    if criteria:
        q["criteria"] = criteria
    return q


def choice(instructions: str, options: Mapping[str, str | None]) -> dict[str, Any]:
    """Pick one of N named options (name -> description)."""
    return {"type": "choice", "instructions": instructions, "criteria": dict(options)}


def score(instructions: str, levels: list[str]) -> dict[str, Any]:
    """Rate on an ordered rubric, lowest level first."""
    return {"type": "score", "instructions": instructions, "criteria": list(levels)}


class Decider:
    def __init__(self, url: str = DEFAULT_URL, timeout: float = 180.0) -> None:
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.calls = 0
        self.last_latency_ms: float = 0.0

    def ask(self, state: Any, questions: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
        body = json.dumps({"state": state, "questions": dict(questions)}).encode()
        req = urllib.request.Request(
            f"{self.url}/v1/systemone", data=body, headers={"content-type": "application/json"}
        )
        t = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read())
        except urllib.error.URLError as exc:
            raise DeciderUnavailable(f"no decider at {self.url} ({exc}). Start one with:\n  {SERVE_HINT}") from exc
        self.calls += 1
        self.last_latency_ms = payload.get("latency_ms") or (time.perf_counter() - t) * 1000
        return payload["answers"]

    def health(self) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(f"{self.url}/health", timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.URLError as exc:
            raise DeciderUnavailable(f"no decider at {self.url} ({exc}). Start one with:\n  {SERVE_HINT}") from exc
