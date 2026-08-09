from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_workflow_can_select_the_bounded_foreign_community_manifest() -> None:
    workflow = (REPOSITORY_ROOT / ".github/workflows/crawl-capability.yml").read_text(
        encoding="utf-8"
    )

    assert "foreign_communities" in workflow
    assert "news_120" in workflow
    assert "foreign-community-sources.yaml" in workflow
    assert "news-sources.yaml" in workflow
    assert "resource-executors.yaml" in workflow
    assert "github_actions_crawl4ai" in workflow
    assert "finance-crawler-capability-report-${{ inputs.scope }}" in workflow
    assert "default: \"1\"" in workflow
    assert "CF_RELAY_BASE_URL: ${{ vars.CF_RELAY_BASE_URL }}" in workflow
    assert "node --test worker/test/index.test.mjs" in workflow
    assert "npm ci --prefix experiments/crawlee-browser" in workflow
    assert "node --test experiments/crawlee-browser/test/*.test.mjs" in workflow
    assert "node --test experiments/cloudflare-browser-run/test/*.test.mjs" in workflow
    assert "experiments/crawlee-browser/scripts/run-crawlee.mjs" in workflow
    assert "artifacts/crawlee-browser.json" in workflow
    assert (
        "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38 # v6.5.0"
        in workflow
    )
