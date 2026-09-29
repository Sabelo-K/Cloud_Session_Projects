import pytest
import requests

from brief import http
from tests.conftest import load_fixture


class Resp:
    def __init__(self, status, body=None, content=b""):
        self.status_code, self._body, self.content = status, body, content

    def json(self):
        if self._body is None:
            raise ValueError("no json")
        return self._body


def patch_get(monkeypatch, *responses):
    calls, queue = [], list(responses)

    def fake(url, params=None, headers=None, timeout=None):
        calls.append({"url": url, "params": params, "headers": headers})
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(http.requests, "get", fake)
    return calls


def test_real_google_error_reason_is_surfaced_and_not_retried(monkeypatch):
    calls = patch_get(monkeypatch, Resp(400, load_fixture("youtube_error_bad_key.json")))
    with pytest.raises(http.HttpError) as err:
        http.get_json("https://www.googleapis.com/youtube/v3/channels")
    assert "HTTP 400: API key not valid. Please pass a valid API key." in str(err.value)
    assert len(calls) == 1


def test_missing_key_error_from_the_real_api_is_readable(monkeypatch):
    patch_get(monkeypatch, Resp(403, load_fixture("youtube_error_no_key.json")))
    with pytest.raises(http.HttpError, match="HTTP 403: Method doesn't allow unregistered callers"):
        http.get_json("https://www.googleapis.com/youtube/v3/channels")


def test_server_errors_are_retried_then_succeed(monkeypatch):
    monkeypatch.setattr(http.time, "sleep", lambda _s: None)
    calls = patch_get(monkeypatch, Resp(503), Resp(200, {"ok": 1}))
    assert http.get_json("https://x.co.za/api") == {"ok": 1} and len(calls) == 2


def test_network_errors_are_retried_then_reported(monkeypatch):
    monkeypatch.setattr(http.time, "sleep", lambda _s: None)
    patch_get(monkeypatch, *[requests.ConnectionError("dns") for _ in range(3)])
    with pytest.raises(http.HttpError, match="ConnectionError: dns after 3 attempts"):
        http.get_json("https://x.co.za/api")


def test_secrets_are_scrubbed_from_error_text(monkeypatch):
    boom = requests.ConnectionError("failed: /v1/channels?key=AIzaSECRET&id=1")
    patch_get(monkeypatch, boom, boom)
    with pytest.raises(http.HttpError) as err:
        http.get_json("https://x.co.za/api", attempts=2, redact=["AIzaSECRET"])
    assert "AIzaSECRET" not in str(err.value) and "***" in str(err.value)


def test_non_json_body_is_an_http_error(monkeypatch):
    patch_get(monkeypatch, Resp(200, None))
    with pytest.raises(http.HttpError, match="not JSON"):
        http.get_json("https://x.co.za/api")


def test_get_bytes_returns_the_body_and_sends_custom_headers(monkeypatch):
    calls = patch_get(monkeypatch, Resp(200, None, b"<rss/>"))
    assert http.get_bytes("https://x.co.za/feed", headers={"Accept": "application/rss+xml"}) == b"<rss/>"
    assert calls[0]["headers"]["Accept"] == "application/rss+xml"
    assert calls[0]["headers"]["User-Agent"] == http.USER_AGENT
