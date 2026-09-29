import pytest
import requests

from brief.telegram import MAX_LEN, TelegramError, send_message

TOKEN = "123456:SECRET-TOKEN"


class Resp:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self._body = {"ok": True} if body is None else body

    def json(self):
        return self._body


def scripted(*responses):
    sent = []
    queue = list(responses)

    def post(url, json, timeout):
        sent.append(json)
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    return post, sent


def test_success_sends_html_without_link_previews():
    post, sent = scripted(Resp())
    send_message("<b>hi</b>", TOKEN, "42", post=post)
    assert sent == [{"chat_id": "42", "text": "<b>hi</b>", "parse_mode": "HTML",
                     "disable_web_page_preview": True}]


def test_rate_limit_is_retried_using_retry_after():
    post, sent = scripted(Resp(429, {"ok": False, "parameters": {"retry_after": 1}}), Resp())
    send_message("hi", TOKEN, "42", post=post)
    assert len(sent) == 2


def test_server_errors_are_retried_then_give_up():
    post, sent = scripted(Resp(502, {"ok": False}), Resp(502, {"ok": False}), Resp(502, {"ok": False}))
    with pytest.raises(TelegramError, match="after 3 attempts"):
        send_message("hi", TOKEN, "42", post=post)
    assert len(sent) == 3


def test_rejected_markup_falls_back_to_plain_text():
    bad = Resp(400, {"ok": False, "description": "Bad Request: can't parse entities: ..."})
    post, sent = scripted(bad, Resp())
    send_message("<b>Tom &amp; Jerry</b>", TOKEN, "42", post=post)
    assert "parse_mode" not in sent[1]
    assert sent[1]["text"] == "Tom & Jerry"


def test_client_errors_are_not_retried_and_do_not_leak_the_token():
    post, sent = scripted(Resp(401, {"ok": False, "description": "Unauthorized"}))
    with pytest.raises(TelegramError) as err:
        send_message("hi", TOKEN, "42", post=post)
    assert len(sent) == 1 and TOKEN not in str(err.value)


def test_network_errors_are_redacted():
    boom = requests.ConnectionError(f"HTTPSConnectionPool: /bot{TOKEN}/sendMessage failed")
    post, _ = scripted(boom, boom, boom)
    with pytest.raises(TelegramError) as err:
        send_message("hi", TOKEN, "42", post=post)
    assert TOKEN not in str(err.value) and "***" in str(err.value)


def test_overlong_message_is_truncated_to_telegrams_limit():
    post, sent = scripted(Resp())
    send_message("x" * (MAX_LEN + 500), TOKEN, "42", post=post)
    assert len(sent[0]["text"]) == MAX_LEN
