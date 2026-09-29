"""Small HTTP GET helpers with timeout and retry, shared by all sections."""
from __future__ import annotations

import logging
import time
from typing import Any, Iterable

import requests

log = logging.getLogger(__name__)

USER_AGENT = "sa-morning-brief/1.0 (personal GitHub Actions job)"
RETRY_STATUS = {429, 500, 502, 503, 504}


class HttpError(Exception):
    pass


def _api_message(resp: requests.Response) -> str:
    """The human-readable reason from a JSON error body (Google APIs: {"error": {"message"}})."""
    try:
        err = resp.json().get("error")
    except (ValueError, AttributeError):
        return ""
    message = err.get("message", "") if isinstance(err, dict) else str(err or "")
    return " ".join(message.split())[:160]


def get_response(url: str, params: dict[str, Any] | None = None, *,
                 headers: dict[str, str] | None = None, timeout: float = 15,
                 attempts: int = 3, redact: Iterable[str] = ()) -> requests.Response:
    """GET with retry on network errors, 429 and 5xx. Any string in `redact` is scrubbed from
    error text. Non-retryable errors (4xx) raise immediately, with the API's own reason if any."""
    secrets = [s for s in redact if s]

    def scrub(text: str) -> str:
        for secret in secrets:
            text = text.replace(secret, "***")
        return text

    all_headers = {"User-Agent": USER_AGENT, **(headers or {})}
    last = "no attempt made"
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.get(url, params=params, headers=all_headers, timeout=timeout)
        except requests.RequestException as exc:
            last = scrub(f"{type(exc).__name__}: {exc}")
        else:
            if resp.status_code == 200:
                return resp
            reason = _api_message(resp)
            last = scrub(f"HTTP {resp.status_code}" + (f": {reason}" if reason else ""))
            if resp.status_code not in RETRY_STATUS:
                raise HttpError(f"{url}: {last}")
        if attempt < attempts:
            time.sleep(2 ** (attempt - 1))
    raise HttpError(f"{url}: {last} after {attempts} attempts")


def get_json(url: str, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
    resp = get_response(url, params, **kwargs)
    try:
        return resp.json()
    except ValueError as exc:
        raise HttpError(f"{url}: response was not JSON ({exc})") from exc


def get_bytes(url: str, params: dict[str, Any] | None = None, **kwargs: Any) -> bytes:
    return get_response(url, params, **kwargs).content
