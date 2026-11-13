"""Local Ollama adapter with deterministic request logging and validation."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


@dataclass
class OllamaResult:
    ok: bool
    payload: dict | None
    error: str | None
    latency_ms: float
    model_digest: str | None


class OllamaClient:
    def __init__(self, model="llama3.1:8b-instruct-q4_K_M", base_url="http://localhost:11434", temperature=0.0, timeout=120, log_path=None):
        self.model, self.base_url, self.temperature, self.timeout, self.log_path = model, base_url.rstrip("/"), temperature, timeout, log_path

    def _log(self, event):
        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, sort_keys=True) + "\n")

    def tags(self):
        req = Request(self.base_url + "/api/tags")
        with urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read())

    def digest(self):
        try:
            for item in self.tags().get("models", []):
                if item.get("name") == self.model:
                    return item.get("digest") or hashlib.sha256(json.dumps(item, sort_keys=True).encode()).hexdigest()
        except Exception:
            return None
        return None

    def generate(self, prompt, *, system=None, schema=None):
        started = time.perf_counter()
        body = {"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": self.temperature}, "format": schema or "json"}
        if system:
            body["system"] = system
        event = {"model": self.model, "temperature": self.temperature, "digest": self.digest(), "request_sha256": hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()}
        try:
            req = Request(self.base_url + "/api/generate", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=self.timeout) as r:
                payload = json.loads(r.read())
            event.update(ok=True, latency_ms=round((time.perf_counter() - started) * 1000, 2), prompt=prompt, system=system, raw_response=payload.get("response"))
            self._log(event)
            return OllamaResult(True, payload, None, event["latency_ms"], event["digest"])
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            event.update(ok=False, latency_ms=round((time.perf_counter() - started) * 1000, 2), error=f"{type(exc).__name__}: {exc}")
            self._log(event)
            return OllamaResult(False, None, event["error"], event["latency_ms"], event["digest"])

