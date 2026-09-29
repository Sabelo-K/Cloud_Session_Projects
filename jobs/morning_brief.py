"""Entrypoint: build the SA Morning Brief and send it to Telegram.

    python -m jobs.morning_brief              # send
    python -m jobs.morning_brief --dry-run    # print only; no Telegram credentials needed
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date, datetime, time

from brief import runner
from brief.config import ConfigError, load_dotenv, load_settings, require_env
from brief.header import build_header
from brief.sections import SECTIONS
from brief.telegram import TelegramError, send_message
from brief.util import SAST, describe, esc, fmt_date_long, now_sast

log = logging.getLogger("morning_brief")


def build_message(settings: dict, now: datetime,
                  dry_run: bool = False) -> tuple[str, list[runner.SectionResult]]:
    ctx = runner.Context(now=now, dry_run=dry_run)
    results = runner.run_sections(SECTIONS, settings, ctx)
    message = runner.assemble(build_header(now.date()), results,
                              settings.get("brief", {}).get("max_lines", 30))
    return message, results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="print the message, don't send it")
    parser.add_argument("--date", type=date.fromisoformat, metavar="YYYY-MM-DD",
                        help="pretend it is this date at 07:00 SAST (calendar/holiday testing; "
                             "live weather/FX still describe the real today)")
    args = parser.parse_args(argv)

    load_dotenv()
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper(),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    for noisy in ("yfinance", "peewee", "urllib3", "curl_cffi", "charset_normalizer"):
        logging.getLogger(noisy).setLevel(max(logging.getLogger().level, logging.WARNING))   # DEBUG shows OUR values only

    settings = load_settings()
    now = datetime.combine(args.date, time(7, 0), tzinfo=SAST) if args.date else now_sast()
    try:
        message, results = build_message(settings, now, dry_run=args.dry_run)
    except Exception as exc:  # noqa: BLE001 - last resort: a broken brief still beats silence
        log.exception("building the brief failed")
        message, results = f"<b>{esc(fmt_date_long(now.date()))}</b>\n⚠️ The brief could not be built " \
                           f"({esc(describe(exc))}). Check the workflow log.", []
    for report in (runner.write_step_summary, runner.annotate_failures):
        try:
            report(results)
        except Exception:  # noqa: BLE001 - reporting must never stop the send
            log.exception("%s failed", report.__name__)

    if args.dry_run:
        print(message)
        return 0
    try:
        send_message(message, require_env("TELEGRAM_BOT_TOKEN"), require_env("TELEGRAM_CHAT_ID"))
    except (ConfigError, TelegramError) as exc:
        log.error("Could not send the brief: %s", exc)
        return 1
    log.info("Brief sent (%d lines, %d chars)", message.count("\n") + 1, len(message))
    return 0


if __name__ == "__main__":
    sys.exit(main())
