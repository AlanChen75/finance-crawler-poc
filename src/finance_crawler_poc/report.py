from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from finance_crawler_poc.models import ProbeResult


@dataclass(frozen=True)
class ReportPaths:
    json_path: Path
    markdown_path: Path


def write_reports(
    results: list[ProbeResult],
    output_dir: Path,
    *,
    generated_at: str,
) -> ReportPaths:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = dict(sorted(Counter(item.outcome.value for item in results).items()))
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "summary": summary,
        "results": [item.to_dict() for item in results],
    }
    json_path = output_dir / "report.json"
    markdown_path = output_dir / "report.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(results, generated_at, summary), encoding="utf-8")
    return ReportPaths(json_path=json_path, markdown_path=markdown_path)


def _render_markdown(
    results: list[ProbeResult], generated_at: str, summary: dict[str, int]
) -> str:
    summary_text = ", ".join(f"{key}={value}" for key, value in summary.items())
    lines = [
        "# Finance crawler capability report",
        "",
        f"Generated: {generated_at}",
        "",
        f"Summary: {summary_text}",
        "",
        "| source | transport | outcome | HTTP | chars | attempts | ms | error |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in results:
        status = str(item.status_code) if item.status_code is not None else "-"
        error = item.error.replace("|", "\\|").replace("\n", " ")[:160]
        lines.append(
            f"| {item.source_id} | {item.transport} | {item.outcome.value} | "
            f"{status} | {item.content_chars} | {item.attempts} | {item.elapsed_ms} | {error} |"
        )
    return "\n".join(lines) + "\n"
