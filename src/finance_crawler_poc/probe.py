from __future__ import annotations

import asyncio
import hashlib
import time
from collections.abc import Awaitable, Callable
from typing import Protocol

from finance_crawler_poc.classification import classify_failure
from finance_crawler_poc.models import FetchResponse, Outcome, ProbeResult, Source


class Adapter(Protocol):
    async def fetch(self, source: Source) -> FetchResponse: ...


Sleep = Callable[[float], Awaitable[None]]
RETRYABLE = frozenset({Outcome.RATE_LIMITED, Outcome.TIMEOUT, Outcome.HTTP_ERROR})


async def probe_source(
    source: Source,
    adapter: Adapter,
    *,
    sleep: Sleep = asyncio.sleep,
    run_index: int = 1,
) -> ProbeResult:
    started = time.perf_counter()
    if not source.enabled:
        return _result(
            source,
            outcome=Outcome.DISABLED,
            attempts=0,
            elapsed_ms=_elapsed_ms(started),
            error=source.disabled_reason,
            run_index=run_index,
        )

    last_result: ProbeResult | None = None
    for attempt in range(1, source.retries + 2):
        try:
            response = await adapter.fetch(source)
        except Exception as exc:  # External adapters are an explicit failure boundary.
            error = f"{type(exc).__name__}: {exc}"
            outcome = classify_failure(status_code=None, error=error, content="")
            last_result = _result(
                source,
                outcome=outcome,
                attempts=attempt,
                elapsed_ms=_elapsed_ms(started),
                error=error,
                run_index=run_index,
            )
        else:
            last_result = _evaluate_response(source, response, attempt, started, run_index)

        if last_result.outcome is Outcome.SUCCESS:
            return last_result
        if last_result.outcome not in RETRYABLE or attempt > source.retries:
            return last_result
        await sleep(float(2 ** (attempt - 1)))

    if last_result is None:  # Defensive invariant; the loop always executes at least once.
        raise RuntimeError("probe loop produced no result")
    return last_result


def _evaluate_response(
    source: Source,
    response: FetchResponse,
    attempt: int,
    started: float,
    run_index: int,
) -> ProbeResult:
    if response.error or response.status_code is None or not 200 <= response.status_code < 400:
        outcome = classify_failure(
            status_code=response.status_code,
            error=response.error,
            content=response.content,
        )
        return _result(
            source,
            outcome=outcome,
            status_code=response.status_code,
            attempts=attempt,
            elapsed_ms=_elapsed_ms(started),
            content=response.content,
            error=response.error or f"HTTP {response.status_code}",
            run_index=run_index,
        )

    barrier_outcome = classify_failure(
        status_code=response.status_code,
        error="",
        content=response.content[:5_000],
    )
    if barrier_outcome in {Outcome.AUTH_REQUIRED, Outcome.BLOCKED, Outcome.ROBOTS_DENIED}:
        barrier_errors = {
            Outcome.AUTH_REQUIRED: "authentication requirement found in response",
            Outcome.BLOCKED: "anti-bot marker found in content",
            Outcome.ROBOTS_DENIED: "robots denial found in response",
        }
        return _result(
            source,
            outcome=barrier_outcome,
            status_code=response.status_code,
            attempts=attempt,
            elapsed_ms=_elapsed_ms(started),
            content=response.content,
            error=barrier_errors[barrier_outcome],
            run_index=run_index,
        )

    lowered_content = response.content.casefold()
    missing_terms = [term for term in source.required_terms if term.casefold() not in lowered_content]
    if missing_terms:
        return _result(
            source,
            outcome=Outcome.INVALID_CONTENT,
            status_code=response.status_code,
            attempts=attempt,
            elapsed_ms=_elapsed_ms(started),
            content=response.content,
            error=f"required term missing: {', '.join(missing_terms)}",
            run_index=run_index,
        )
    if len(response.content) < source.min_content_chars:
        return _result(
            source,
            outcome=Outcome.INVALID_CONTENT,
            status_code=response.status_code,
            attempts=attempt,
            elapsed_ms=_elapsed_ms(started),
            content=response.content,
            error=(
                f"content shorter than minimum: {len(response.content)} "
                f"< {source.min_content_chars}"
            ),
            run_index=run_index,
        )

    return _result(
        source,
        outcome=Outcome.SUCCESS,
        status_code=response.status_code,
        attempts=attempt,
        elapsed_ms=_elapsed_ms(started),
        content=response.content,
        run_index=run_index,
    )


def _result(
    source: Source,
    *,
    outcome: Outcome,
    attempts: int,
    elapsed_ms: int,
    status_code: int | None = None,
    content: str = "",
    error: str = "",
    run_index: int = 1,
) -> ProbeResult:
    normalized_preview = " ".join(content.split())[:500]
    return ProbeResult(
        source_id=source.id,
        name=source.name,
        topic=source.topic,
        transport=source.transport,
        url=source.url,
        outcome=outcome,
        status_code=status_code,
        attempts=attempts,
        elapsed_ms=elapsed_ms,
        content_chars=len(content),
        content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest() if content else "",
        preview=normalized_preview,
        error=error,
        kind=source.kind,
        provenance=source.provenance,
        selection_evidence=source.selection_evidence,
        run_index=run_index,
        community_type=source.community_type,
        region=source.region,
        access_tier=source.access_tier,
    )


def _elapsed_ms(started: float) -> int:
    return max(0, round((time.perf_counter() - started) * 1_000))
