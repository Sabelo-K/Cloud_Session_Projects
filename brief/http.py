"""One tiny JSON GET helper with timeout and retry, shared by all API sections."""
from __future__ import annotations

import logging
import time
from typing import Any

import requests

log = logging.getLogger(__name__)

USER_AGENT = "sa-morning-brief/1.0 (personal GitHub Actions job)"
RETRY_STATUS = {429, 500, 502, 503, 504}


class HttpError(Exception):
    pass


def get_json(url: str, params: dict[str, Any] | None = None, *, timeout: float = 15,
             attempts: int = 3) -> Any:
    last: str = "no attempt made"
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.get(url, params=params, timeout=timeout,
                                headers={"User-Agent": USER_AGENT})
        except requests.RequestException as exc:
            last = f"{type(exc).__name__}: {exc}"
        else:
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError as exc:
                    raise HttpError(f"{url}: response was not JSON ({exc})") from exc
            last = f"HTTP {resp.status_code}"
            if resp.status_code not in RETRY_STATUS:
                raise HttpError(f"{url}: {last}")
        if attempt < attempts:
            time.sleep(2 ** (attempt - 1))
    raise HttpError(f"{url}: {last} after {attempts} attempts")
