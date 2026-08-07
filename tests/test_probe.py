import asyncio

from finance_crawler_poc.models import FetchResponse, Outcome, Source
from finance_crawler_poc.probe import probe_source


class FakeAdapter:
    def __init__(self, responses: list[FetchResponse | Exception]) -> None:
        self.responses = list(responses)
        self.calls = 0

    async def fetch(self, source: Source) -> FetchResponse:
        response = self.responses[self.calls]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response


def make_source(**overrides: object) -> Source:
    values: dict[str, object] = {
        "id": "source",
        "name": "Source",
        "topic": "finance",
        "transport": "browser",
        "url": "https://example.com",
        "required_terms": ("Market",),
        "min_content_chars": 10,
        "timeout_seconds": 10,
        "retries": 1,
    }
    values.update(overrides)
    return Source(**values)


def test_probe_requires_content_contract_not_only_http_200() -> None:
    adapter = FakeAdapter([FetchResponse(status_code=200, content="too short")])

    result = asyncio.run(probe_source(make_source(retries=0), adapter, sleep=lambda _: _done()))

    assert result.outcome is Outcome.INVALID_CONTENT
    assert "required term" in result.error


def test_probe_retries_rate_limit_and_records_success_evidence() -> None:
    adapter = FakeAdapter(
        [
            FetchResponse(status_code=429, content="slow down"),
            FetchResponse(status_code=200, content="Market data is available today"),
        ]
    )

    result = asyncio.run(probe_source(make_source(), adapter, sleep=lambda _: _done()))

    assert result.outcome is Outcome.SUCCESS
    assert result.attempts == 2
    assert result.content_chars == 30
    assert len(result.content_sha256) == 64
    assert result.preview == "Market data is available today"


def test_probe_converts_exception_to_classified_result() -> None:
    adapter = FakeAdapter([TimeoutError("operation timed out")])

    result = asyncio.run(probe_source(make_source(retries=0), adapter, sleep=lambda _: _done()))

    assert result.outcome is Outcome.TIMEOUT
    assert result.attempts == 1


def test_probe_records_http_failure_and_content_evidence() -> None:
    adapter = FakeAdapter([FetchResponse(status_code=503, content="maintenance")])

    result = asyncio.run(probe_source(make_source(retries=0), adapter, sleep=lambda _: _done()))

    assert result.outcome is Outcome.HTTP_ERROR
    assert result.status_code == 503
    assert result.error == "HTTP 503"
    assert result.content_chars == len("maintenance")


def test_probe_rejects_antibot_page_returned_with_http_200() -> None:
    adapter = FakeAdapter([FetchResponse(status_code=200, content="Cloudflare CAPTCHA" * 20)])

    result = asyncio.run(probe_source(make_source(retries=0), adapter, sleep=lambda _: _done()))

    assert result.outcome is Outcome.BLOCKED
    assert result.error == "anti-bot marker found in content"


def test_probe_rejects_content_below_minimum_after_terms_pass() -> None:
    adapter = FakeAdapter([FetchResponse(status_code=200, content="Market")])

    result = asyncio.run(probe_source(make_source(retries=0), adapter, sleep=lambda _: _done()))

    assert result.outcome is Outcome.INVALID_CONTENT
    assert result.error == "content shorter than minimum: 6 < 10"


def test_disabled_source_never_calls_adapter() -> None:
    adapter = FakeAdapter([])

    result = asyncio.run(
        probe_source(
            make_source(enabled=False, disabled_reason="identity required"),
            adapter,
            sleep=lambda _: _done(),
        )
    )

    assert result.outcome is Outcome.DISABLED
    assert result.error == "identity required"
    assert adapter.calls == 0


async def _done() -> None:
    return None
