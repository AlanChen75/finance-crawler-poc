from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_workflow_can_select_the_bounded_foreign_community_manifest() -> None:
    workflow = (REPOSITORY_ROOT / ".github/workflows/crawl-capability.yml").read_text(
        encoding="utf-8"
    )

    assert "foreign_communities" in workflow
    assert "foreign-community-sources.yaml" in workflow
    assert "finance-crawler-capability-report-${{ inputs.scope }}" in workflow
    assert "default: \"1\"" in workflow
    assert "CF_RELAY_BASE_URL: ${{ vars.CF_RELAY_BASE_URL }}" in workflow
    assert "node --test worker/test/index.test.mjs" in workflow
