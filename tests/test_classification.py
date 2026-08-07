import pytest

from finance_crawler_poc.classification import classify_failure
from finance_crawler_poc.models import Outcome


@pytest.mark.parametrize(
    ("status_code", "error", "content", "expected"),
    [
        (429, "", "", Outcome.RATE_LIMITED),
        (403, "", "Access denied", Outcome.BLOCKED),
        (200, "", "Cloudflare CAPTCHA challenge", Outcome.BLOCKED),
        (None, "certificate verify failed", "", Outcome.TLS_ERROR),
        (None, "operation timed out", "", Outcome.TIMEOUT),
        (503, "service unavailable", "", Outcome.HTTP_ERROR),
        (None, "browser crashed", "", Outcome.ERROR),
    ],
)
def test_classify_failure(
    status_code: int | None,
    error: str,
    content: str,
    expected: Outcome,
) -> None:
    assert classify_failure(status_code=status_code, error=error, content=content) is expected
