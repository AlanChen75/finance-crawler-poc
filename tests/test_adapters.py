import asyncio
import json
import sys
from types import SimpleNamespace

import httpx

from finance_crawler_poc.adapters import Crawl4AIAdapter, HttpAdapter, _markdown_text
from finance_crawler_poc.models import Source


def source(transport: str) -> Source:
    return Source(
        id="source",
        name="Source",
        topic="finance",
        transport=transport,
        url="https://example.com/data",
        required_terms=(),
    )


def test_http_adapter_normalizes_json_for_contract_validation() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["User-Agent"].startswith("FinanceCrawlerCapabilityProbe/")
        return httpx.Response(200, json={"price": 42})

    adapter = HttpAdapter(transport=httpx.MockTransport(handler))
    response = asyncio.run(adapter.fetch(source("json_api")))
    asyncio.run(adapter.close())

    assert response.status_code == 200
    assert json.loads(response.content) == {"price": 42}


def test_http_adapter_reports_invalid_json_without_throwing() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json")

    adapter = HttpAdapter(transport=httpx.MockTransport(handler))
    response = asyncio.run(adapter.fetch(source("json_api")))
    asyncio.run(adapter.close())

    assert response.error.startswith("invalid JSON:")
    assert response.content == "not json"


def test_crawl4ai_adapter_enforces_robots_and_page_timeout(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class RunConfig:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    fake_module = SimpleNamespace(CacheMode=SimpleNamespace(BYPASS="bypass"), CrawlerRunConfig=RunConfig)
    monkeypatch.setitem(sys.modules, "crawl4ai", fake_module)

    class Crawler:
        async def arun(self, *, url: str, config: object) -> object:
            assert url == "https://example.com/data"
            assert isinstance(config, RunConfig)
            return SimpleNamespace(
                markdown=SimpleNamespace(raw_markdown="market evidence"),
                status_code=200,
                success=True,
            )

    adapter = Crawl4AIAdapter()
    adapter._crawler = Crawler()
    response = asyncio.run(adapter.fetch(source("browser")))

    assert response.content == "market evidence"
    assert captured["check_robots_txt"] is True
    assert captured["page_timeout"] == 40_000
    assert captured["delay_before_return_html"] == 1.0


def test_markdown_text_handles_none_raw_and_plain_values() -> None:
    assert _markdown_text(None) == ""
    assert _markdown_text(SimpleNamespace(raw_markdown="raw")) == "raw"
    assert _markdown_text("plain") == "plain"
