from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class Outcome(str, Enum):
    SUCCESS = "success"
    AUTH_REQUIRED = "auth_required"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    TLS_ERROR = "tls_error"
    TIMEOUT = "timeout"
    ROBOTS_DENIED = "robots_denied"
    HTTP_ERROR = "http_error"
    INVALID_CONTENT = "invalid_content"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    topic: str
    transport: str
    url: str
    required_terms: tuple[str, ...] = ()
    min_content_chars: int = 300
    timeout_seconds: int = 40
    retries: int = 1
    enabled: bool = True
    disabled_reason: str = ""
    provenance: str = "curated"
    kind: str = "other"
    selection_evidence: str = ""
    community_type: str = "not_applicable"
    region: str = "global"
    access_tier: str = "public_web"


@dataclass(frozen=True)
class Manifest:
    version: int
    sources: tuple[Source, ...]


@dataclass(frozen=True)
class FetchResponse:
    status_code: int | None
    content: str
    error: str = ""


@dataclass(frozen=True)
class ProbeResult:
    source_id: str
    name: str
    topic: str
    transport: str
    url: str
    outcome: Outcome
    status_code: int | None
    attempts: int
    elapsed_ms: int
    content_chars: int
    content_sha256: str
    preview: str
    error: str
    kind: str = "other"
    provenance: str = "curated"
    selection_evidence: str = ""
    run_index: int = 1
    community_type: str = "not_applicable"
    region: str = "global"
    access_tier: str = "public_web"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["outcome"] = self.outcome.value
        return payload
