from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_workflow_can_select_the_bounded_foreign_community_manifest() -> None:
    workflow = (REPOSITORY_ROOT / ".github/workflows/crawl-capability.yml").read_text(
        encoding="utf-8"
    )

    assert "foreign_communities" in workflow
    assert "foreign-community-sources.yaml" in workflow
    assert "finance-crawler-capability-report-${{ inputs.scope }}" in workflow
