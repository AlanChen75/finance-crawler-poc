from pathlib import Path

import pytest

from finance_crawler_poc.manifest import ManifestError, load_manifest


def write_manifest(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "sources.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_load_manifest_applies_defaults_and_preserves_disabled_reason(tmp_path: Path) -> None:
    path = write_manifest(
        tmp_path,
        """
version: 1
defaults:
  timeout_seconds: 12
  retries: 2
  min_content_chars: 50
sources:
  - id: api
    name: API
    topic: prices
    kind: official_data
    transport: json_api
    url: https://example.com/data.json
    selection_evidence: https://example.com/docs
    required_terms: [price]
  - id: sec
    name: SEC
    topic: filings
    transport: browser
    url: https://www.sec.gov/edgar
    enabled: false
    disabled_reason: contact identity required
""",
    )

    manifest = load_manifest(path)

    assert manifest.version == 1
    assert manifest.sources[0].timeout_seconds == 12
    assert manifest.sources[0].retries == 2
    assert manifest.sources[0].min_content_chars == 50
    assert manifest.sources[0].kind == "official_data"
    assert manifest.sources[0].selection_evidence == "https://example.com/docs"
    assert manifest.sources[1].enabled is False
    assert manifest.sources[1].disabled_reason == "contact identity required"


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (
            """
version: 1
sources:
  - {id: duplicate, name: A, topic: x, transport: rss, url: https://a.example/rss}
  - {id: duplicate, name: B, topic: y, transport: rss, url: https://b.example/rss}
""",
            "duplicate source id",
        ),
        (
            """
version: 1
sources:
  - {id: bad_url, name: Bad, topic: x, transport: browser, url: file:///etc/passwd}
""",
            "http or https",
        ),
        (
            """
version: 1
sources:
  - {id: bad_transport, name: Bad, topic: x, transport: ftp, url: https://example.com}
""",
            "transport",
        ),
        (
            """
version: 1
sources:
  - {id: disabled, name: Bad, topic: x, transport: browser, url: https://example.com, enabled: false}
""",
            "disabled_reason",
        ),
        (
            """
version: 1
sources:
  - {id: local_ip, name: Bad, topic: x, transport: browser, url: http://127.0.0.1/admin}
""",
            "public host",
        ),
        (
            """
version: 1
sources:
  - {id: credentials, name: Bad, topic: x, transport: browser, url: https://user:pass@example.com}
""",
            "credentials",
        ),
        (
            """
version: 1
sources:
  - {id: bad_kind, name: Bad, topic: x, kind: influencer, transport: browser, url: https://example.com}
""",
            "kind",
        ),
        (
            """
version: 1
sources:
  - {id: bad_evidence, name: Bad, topic: x, transport: browser, url: https://example.com, selection_evidence: file:///tmp/note}
""",
            "selection_evidence",
        ),
    ],
)
def test_manifest_rejects_invalid_boundary_input(tmp_path: Path, body: str, message: str) -> None:
    with pytest.raises(ManifestError, match=message):
        load_manifest(write_manifest(tmp_path, body))
