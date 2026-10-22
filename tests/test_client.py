import pytest

from conftest import FakeSession, Resp
from ph_dataset.client import TOKEN_URL, APIError, AuthError, PHClient


def test_requires_credentials(monkeypatch):
    for k in ("PH_TOKEN", "PH_CLIENT_ID", "PH_CLIENT_SECRET"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(AuthError):
        PHClient()


def test_client_credentials_auth_and_no_mock_fallback():
    s = FakeSession([Resp(401)])
    c = PHClient(client_id="a", client_secret="b", session=s)
    with pytest.raises(AuthError):
        c.query("{x}")
    assert s.calls[0]["url"] == TOKEN_URL


def test_auth_then_query():
    s = FakeSession([Resp(200, {"access_token": "T"}), Resp(200, {"data": {"ok": 1}})])
    c = PHClient(client_id="a", client_secret="b", session=s)
    assert c.query("{x}") == {"ok": 1}
    assert s.calls[1]["headers"]["Authorization"] == "Bearer T"


def test_429_waits_for_reset_header(sleeps):
    s = FakeSession([Resp(429, headers={"X-Rate-Limit-Reset": "10"}), Resp(200, {"data": {"ok": 1}})])
    c = PHClient(token="t", session=s, sleep=sleeps.append)
    assert c.query("{x}") == {"ok": 1}
    assert sleeps == [12]


def test_proactive_throttle_when_low_remaining(sleeps):
    s = FakeSession([Resp(200, {"data": {}}, {"X-Rate-Limit-Remaining": "50", "X-Rate-Limit-Reset": "30"})])
    PHClient(token="t", session=s, sleep=sleeps.append).query("{x}")
    assert sleeps == [31]


def test_gives_up_after_retries(sleeps):
    s = FakeSession([Resp(500)] * 3)
    c = PHClient(token="t", session=s, sleep=sleeps.append, max_retries=2)
    with pytest.raises(APIError):
        c.query("{x}")


def test_graphql_errors_raise():
    s = FakeSession([Resp(200, {"errors": [{"message": "bad"}]})])
    with pytest.raises(APIError):
        PHClient(token="t", session=s).query("{x}")


def test_401_reports_ph_error_code():
    s = FakeSession([Resp(401, {"errors": [{"error": "invalid_oauth_token"}]})])
    with pytest.raises(AuthError, match="invalid_oauth_token"):
        PHClient(token="t", session=s).query("{x}")


def test_token_whitespace_and_quotes_stripped():
    assert PHClient(token=' "abc" \n').token == "abc"
