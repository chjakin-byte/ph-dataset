import pytest


class Resp:
    def __init__(self, status=200, json_data=None, headers=None, text=""):
        self.status_code = status
        self._j = json_data or {}
        self.headers = headers or {}
        self.text = text

    def json(self):
        return self._j


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        r = self.responses.pop(0)
        return r(json) if callable(r) else r


@pytest.fixture
def sleeps():
    return []


@pytest.fixture(autouse=True)
def _no_real_credentials(monkeypatch):
    """Tests must never use real credentials from the environment."""
    for k in ("PH_TOKEN", "PH_CLIENT_ID", "PH_CLIENT_SECRET"):
        monkeypatch.delenv(k, raising=False)
