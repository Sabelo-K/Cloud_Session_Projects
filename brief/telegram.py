"""Send the brief to Telegram (Bot API sendMessage, HTML parse mode)."""
from __future__ import annotations

import html
import logging
import re
import time
from typing import Callable

import requests

log = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/sendMessage"
MAX_LEN = 4096  # Telegram's hard limit per message


class TelegramError(Exception):
    pass


def _plain(text: str) -> str:
    return html.unescape(re.sub(r"</?[a-zA-Z][^>]*>", "", text))


def send_message(text: str, token: str, chat_id: str, *,
                 post: Callable[..., requests.Response] = requests.post,
                 attempts: int = 3) -> None:
    """Send `text`. Retries 429/5xx/network errors; if Telegram rejects the HTML, resends as
    plain text so a markup slip never costs you the whole brief. Never leaks the token."""
    if len(text) > MAX_LEN:
        text = text[: MAX_LEN - 1] + "…"

    def redact(msg: str) -> str:
        return msg.replace(token, "***")

    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
               "disable_web_page_preview": True}
    url = API_URL.format(token=token)
    fell_back = False
    last = "no attempt made"

    for attempt in range(1, attempts + 1):
        try:
            resp = post(url, json=payload, timeout=20)
        except requests.RequestException as exc:
            last = redact(f"{type(exc).__name__}: {exc}")
        else:
            try:
                body = resp.json()
            except ValueError:
                body = {}
            if resp.status_code == 200 and body.get("ok"):
                return
            description = str(body.get("description", ""))
            last = redact(f"HTTP {resp.status_code} {description}".strip())
            if resp.status_code == 400 and "parse entities" in description and not fell_back:
                log.warning("Telegram rejected the HTML; resending as plain text")
                payload = {"chat_id": chat_id, "text": _plain(text),
                           "disable_web_page_preview": True}
                fell_back = True
                continue
            if resp.status_code not in (429, 500, 502, 503, 504):
                raise TelegramError(last)
            if resp.status_code == 429:
                retry_after = body.get("parameters", {}).get("retry_after", 2)
                time.sleep(min(float(retry_after), 30))
                continue
        if attempt < attempts:
            time.sleep(2 ** (attempt - 1))
    raise TelegramError(f"Telegram send failed after {attempts} attempts: {last}")
