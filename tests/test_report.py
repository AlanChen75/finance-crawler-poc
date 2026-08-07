import json
from pathlib import Path

from finance_crawler_poc.models import Outcome, ProbeResult
from finance_crawler_poc.report import write_reports


def result(source_id: str, outcome: Outcome) -> ProbeResult:
    return ProbeResult(
        source_id=source_id,
        name=source_id,
        topic="finance",
        transport="browser",
        url=f"https://example.com/{source_id}",
        outcome=outcome,
        status_code=200 if outcome is Outcome.SUCCESS else None,
        attempts=1,
        elapsed_ms=123,
        content_chars=100 if outcome is Outcome.SUCCESS else 0,
        content_sha256="a" * 64 if outcome is Outcome.SUCCESS else "",
        preview="evidence" if outcome is Outcome.SUCCESS else "",
        error="" if outcome is Outcome.SUCCESS else "blocked",
    )


def test_write_reports_emits_machine_and_human_readable_contract(tmp_path: Path) -> None:
    paths = write_reports(
        [result("ok", Outcome.SUCCESS), result("no", Outcome.BLOCKED)],
        tmp_path,
        generated_at="2026-08-07T00:00:00Z",
    )

    payload = json.loads(paths.json_path.read_text(encoding="utf-8"))
    markdown = paths.markdown_path.read_text(encoding="utf-8")

    assert payload["schema_version"] == 1
    assert payload["summary"] == {"blocked": 1, "success": 1}
    assert [item["source_id"] for item in payload["results"]] == ["ok", "no"]
    assert "| ok | browser | success | 200 |" in markdown
    assert "| no | browser | blocked | - |" in markdown
