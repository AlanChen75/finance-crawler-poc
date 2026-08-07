from __future__ import annotations

from finance_crawler_poc.models import Outcome


BLOCK_MARKERS = (
    "access denied",
    "captcha",
    "cloudflare",
    "akamai",
    "datadome",
    "verify you are human",
    "bot detection",
)
TLS_MARKERS = (
    "certificate verify failed",
    "ssl certificate",
    "tls",
    "cert_verify_failed",
)
TIMEOUT_MARKERS = ("timed out", "timeout")
ROBOTS_MARKERS = ("robots.txt", "robots denied", "disallowed by robots")


def classify_failure(*, status_code: int | None, error: str, content: str) -> Outcome:
    combined = f"{error}\n{content}".lower()
    if status_code == 429:
        return Outcome.RATE_LIMITED
    if any(marker in combined for marker in ROBOTS_MARKERS):
        return Outcome.ROBOTS_DENIED
    if any(marker in combined for marker in TLS_MARKERS):
        return Outcome.TLS_ERROR
    if any(marker in combined for marker in TIMEOUT_MARKERS):
        return Outcome.TIMEOUT
    if status_code in {401, 403} or any(marker in combined for marker in BLOCK_MARKERS):
        return Outcome.BLOCKED
    if status_code is not None and status_code >= 400:
        return Outcome.HTTP_ERROR
    return Outcome.ERROR
