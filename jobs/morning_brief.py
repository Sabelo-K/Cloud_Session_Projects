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
from brief.sections import SECTIONS
from brief.telegram import TelegramError, send_message
from brief.util import SAST, esc, fmt_date_long, now_sast

log = logging.getLogger("morning_brief")


def build_message(settings: dict, now: datetime) -> tuple[str, list[runner.SectionResult]]:
    ctx = runner.Context(now=now)
    results = runner.run_sections(SECTIONS, settings, ctx)
    header = f"<b>{esc(fmt_date_long(now.date()))}</b>"
    message = runner.assemble(header, results, settings.get("brief", {}).get("max_lines", 30))
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

    settings = load_settings()
    now = datetime.combine(args.date, time(7, 0), tzinfo=SAST) if args.date else now_sast()
    message, results = build_message(settings, now)
    runner.write_step_summary(results)
    runner.annotate_failures(results)

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
