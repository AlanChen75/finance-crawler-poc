from __future__ import annotations

import json
from typing import Any

import httpx

from finance_crawler_poc.models import FetchResponse, Source


USER_AGENT = (
    "FinanceCrawlerCapabilityProbe/0.1 "
    "(+https://github.com/AlanChen75/finance-crawler-poc)"
)


class HttpAdapter:
    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._client = httpx.AsyncClient(
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
            http2=transport is None,
            transport=transport,
        )

    async def fetch(self, source: Source) -> FetchResponse:
        response = await self._client.get(source.url, timeout=source.timeout_seconds)
        content = response.text
        if source.transport == "json_api" and 200 <= response.status_code < 400:
            try:
                parsed: Any = response.json()
            except json.JSONDecodeError as exc:
                return FetchResponse(
                    status_code=response.status_code,
                    content=content,
                    error=f"invalid JSON: {exc}",
                )
            content = json.dumps(parsed, ensure_ascii=False, sort_keys=True)
        return FetchResponse(status_code=response.status_code, content=content)

    async def close(self) -> None:
        await self._client.aclose()


class Crawl4AIAdapter:
    """Lazy adapter so API/RSS probes still run if Chromium initialization fails."""

    def __init__(self) -> None:
        self._crawler: Any = None
        self._context: Any = None
        self._init_error: Exception | None = None

    async def fetch(self, source: Source) -> FetchResponse:
        await self._ensure_crawler()
        if self._init_error is not None:
            raise RuntimeError(f"Crawl4AI initialization failed: {self._init_error}")

        from crawl4ai import CacheMode, CrawlerRunConfig

        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            check_robots_txt=True,
            delay_before_return_html=1.0,
            page_timeout=source.timeout_seconds * 1_000,
            wait_until="domcontentloaded",
        )
        result = await self._crawler.arun(url=source.url, config=config)
        markdown = _markdown_text(result.markdown)
        return FetchResponse(
            status_code=getattr(result, "status_code", None),
            content=markdown,
            error="" if result.success else str(getattr(result, "error_message", "crawl failed")),
        )

    async def _ensure_crawler(self) -> None:
        if self._crawler is not None or self._init_error is not None:
            return
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig

            browser_config = BrowserConfig(
                headless=True,
                user_agent=USER_AGENT,
                verbose=False,
            )
            self._context = AsyncWebCrawler(config=browser_config)
            self._crawler = await self._context.__aenter__()
        except Exception as exc:  # Keep a stable failure for every browser source.
            self._init_error = exc

    async def close(self) -> None:
        if self._context is not None:
            await self._context.__aexit__(None, None, None)


def _markdown_text(markdown: Any) -> str:
    if markdown is None:
        return ""
    raw_markdown = getattr(markdown, "raw_markdown", None)
    return str(raw_markdown if raw_markdown is not None else markdown)
