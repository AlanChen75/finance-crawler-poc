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
        "schema_version": 2,
        "generated_at": generated_at,
        "summary": summary,
        "breakdown": {
            "by_transport": _breakdown(results, "transport"),
            "by_kind": _breakdown(results, "kind"),
        },
        "source_stability": _source_stability(results),
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
        "## Source stability",
        "",
        "| source | kind | transport | success/runs | outcomes |",
        "|---|---|---|---:|---|",
    ]
    stability = _source_stability(results)
    first_result = {item.source_id: item for item in results}
    for item in stability:
        source = first_result[item["source_id"]]
        outcomes = ", ".join(f"{key}={value}" for key, value in item["outcomes"].items())
        lines.append(
            f"| {item['source_id']} | {source.kind} | {source.transport} | "
            f"{item['successes']}/{item['observations']} | {outcomes} |"
        )
    lines.extend(
        [
            "",
            "## Observations",
            "",
            "| run | source | kind | transport | outcome | HTTP | chars | attempts | ms | error |",
            "|---:|---|---|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in results:
        status = str(item.status_code) if item.status_code is not None else "-"
        error = item.error.replace("|", "\\|").replace("\n", " ")[:160]
        lines.append(
            f"| {item.run_index} | {item.source_id} | {item.kind} | {item.transport} | "
            f"{item.outcome.value} | "
            f"{status} | {item.content_chars} | {item.attempts} | {item.elapsed_ms} | {error} |"
        )
    return "\n".join(lines) + "\n"


def _breakdown(results: list[ProbeResult], field: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = {}
    for item in results:
        key = str(getattr(item, field))
        grouped.setdefault(key, Counter())[item.outcome.value] += 1
    return {
        key: dict(sorted(counts.items()))
        for key, counts in sorted(grouped.items())
    }


def _source_stability(results: list[ProbeResult]) -> list[dict[str, object]]:
    grouped: dict[str, Counter[str]] = {}
    for item in results:
        grouped.setdefault(item.source_id, Counter())[item.outcome.value] += 1
    return [
        {
            "source_id": source_id,
            "observations": sum(outcomes.values()),
            "successes": outcomes.get("success", 0),
            "outcomes": dict(sorted(outcomes.items())),
        }
        for source_id, outcomes in grouped.items()
    ]
