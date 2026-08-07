import json
from pathlib import Path

from finance_crawler_poc.models import Outcome, ProbeResult
from finance_crawler_poc.report import write_reports


def result(
    source_id: str,
    outcome: Outcome,
    *,
    transport: str = "browser",
    kind: str = "community",
    run_index: int = 1,
) -> ProbeResult:
    return ProbeResult(
        source_id=source_id,
        name=source_id,
        topic="finance",
        transport=transport,
        url=f"https://example.com/{source_id}",
        outcome=outcome,
        status_code=200 if outcome is Outcome.SUCCESS else None,
        attempts=1,
        elapsed_ms=123,
        content_chars=100 if outcome is Outcome.SUCCESS else 0,
        content_sha256="a" * 64 if outcome is Outcome.SUCCESS else "",
        preview="evidence" if outcome is Outcome.SUCCESS else "",
        error="" if outcome is Outcome.SUCCESS else "blocked",
        kind=kind,
        provenance="test",
        run_index=run_index,
    )


def test_write_reports_emits_machine_and_human_readable_contract(tmp_path: Path) -> None:
    paths = write_reports(
        [
            result("ok", Outcome.SUCCESS),
            result("ok", Outcome.SUCCESS, run_index=2),
            result("no", Outcome.BLOCKED, transport="json_api", kind="market_data"),
            result(
                "no",
                Outcome.AUTH_REQUIRED,
                transport="json_api",
                kind="market_data",
                run_index=2,
            ),
        ],
        tmp_path,
        generated_at="2026-08-07T00:00:00Z",
    )

    payload = json.loads(paths.json_path.read_text(encoding="utf-8"))
    markdown = paths.markdown_path.read_text(encoding="utf-8")

    assert payload["schema_version"] == 2
    assert payload["summary"] == {"auth_required": 1, "blocked": 1, "success": 2}
    assert payload["breakdown"]["by_transport"] == {
        "browser": {"success": 2},
        "json_api": {"auth_required": 1, "blocked": 1},
    }
    assert payload["breakdown"]["by_kind"] == {
        "community": {"success": 2},
        "market_data": {"auth_required": 1, "blocked": 1},
    }
    assert payload["source_stability"] == [
        {"source_id": "ok", "observations": 2, "successes": 2, "outcomes": {"success": 2}},
        {
            "source_id": "no",
            "observations": 2,
            "successes": 0,
            "outcomes": {"auth_required": 1, "blocked": 1},
        },
    ]
    assert [item["source_id"] for item in payload["results"]] == ["ok", "ok", "no", "no"]
    assert "| ok | community | browser | 2/2 | success=2 |" in markdown
    assert "| 2 | no | market_data | json_api | auth_required | - |" in markdown
