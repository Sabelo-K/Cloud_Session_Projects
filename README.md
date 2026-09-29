# SA Morning Brief

One Telegram message every morning (~07:00 SAST) with what matters to a Durban-based data analyst
following South African markets: weather, the rand, JSE/commodities and (from Phase 2) your YouTube
channels, SA economy headlines and a "watch today" line.

Runs entirely on free tiers: GitHub Actions for scheduling, free public APIs for data, Telegram for
delivery. Secrets live only in GitHub Actions secrets.

> **Status: Phase 1 of 3.** Built: weather, rand, markets, Telegram sending, scheduling, manual
> trigger. Coming: YouTube channels, RSS headlines, holiday header, "watch today" (Phase 2); more
> tests and polish (Phase 3).

## Example (illustrative fixture data, not live numbers)

```
Tuesday 29 September 2026

Durban today
17–24°C · rain 40% (3 mm) · wind SW 22 km/h, gusts 41

Rand · ECB Mon 28 Sep
USD/ZAR  17.85  ▲ 0.3%
EUR/ZAR  20.88  ▼ 0.1%
GBP/ZAR  24.00  ▬ 0.0%

Markets (previous close)
JSE Top 40  101,317  ▲ 0.8%
Standard Bank  R285.40  ▲ 1.9%
FirstRand  R89.10  ▼ 1.0%
Absa  R220.00  ▬ 0.0%
Nedbank  R267.34  ▲ 0.1%
Capitec  R3,030.00  ▲ 1.0%
Brent  $97.51  ▼ 2.1%
Gold  $4,150  ▼ 0.5%
```

## Setup (do these in order)

1. **Create a Telegram bot.** In Telegram, message [@BotFather](https://t.me/BotFather), send
   `/newbot`, follow the prompts, and copy the **bot token** it gives you.
2. **Get your chat ID.** Open a chat with your new bot and send it any message (e.g. `/start`; a bot
   can't message you until you've messaged it). Then open
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser and copy the number in
   `"chat":{"id":...}`. (Alternative: message [@userinfobot](https://t.me/userinfobot).)
3. **Get this code onto the repository's default branch.** GitHub only lists a workflow, and only
   runs its schedule, once it's on the default branch.
4. **Add two repository secrets:** *Settings → Secrets and variables → Actions → New repository
   secret*: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
5. **Dry-run to verify every data source.** *Actions → Morning Brief → Run workflow*, tick
   **Dry run**. Open the run: the log prints the message and the run's **Summary** lists each section
   as `ok` / `partial` / `failed`. Check every ticker shows a number (not `unavailable`); a wrong
   ticker or a blocked source is reported per line, with the reason, in the log.
6. **Send a real one.** Run the workflow again with Dry run unticked. The message should land in
   Telegram.
7. **Done.** It now runs daily at 05:00 UTC (07:00 SAST).

## Run locally

```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest                                   # no network needed
cp .env.example .env                     # then fill in the two Telegram values
python -m jobs.morning_brief --dry-run   # print only, no Telegram needed
python -m jobs.morning_brief             # send for real
```

Useful flags: `LOG_LEVEL=DEBUG` shows the raw values fetched per source. `--date 2026-09-25`
pretends it's that morning, to check holiday/market-closed behaviour (live weather/FX still describe
the real today, so those sections may report failures for other dates).

## Configuration

Everything you'd want to edit is in [`config/settings.toml`](config/settings.toml): location,
currency pairs, the ticker list (each is a `[[markets.instruments]]` block), the line limit, extra JSE
closure dates, and `enabled = false` switches per section.

## Data sources

| Section | Source | Key needed |
|---|---|---|
| Weather | [Open-Meteo](https://open-meteo.com) forecast API, Durban (-29.86, 31.03) | No |
| Rand | [Frankfurter](https://frankfurter.dev): ECB reference rates, **published once per business day** (~16:00 CET), so Monday's brief shows Friday's rates. The heading always states the date. | No |
| Markets | Yahoo Finance via [`yfinance`](https://github.com/ranaroussi/yfinance): **unofficial**, can break or rate-limit | No |

### Yahoo tickers

| Line | Ticker | Notes |
|---|---|---|
| JSE Top 40 | `^J200.JO` | Index points |
| Standard Bank | `SBK.JO` | |
| FirstRand | `FSR.JO` | |
| Absa | `ABG.JO` | |
| Nedbank | `NED.JO` | |
| Capitec | `CPI.JO` | Ordinary shares. **Not** `CPIP.JO`, which is the preference share. |
| Brent crude | `BZ=F` | Front-month future, USD/bbl |
| Gold | `GC=F` | COMEX front-month future, USD/oz. The % change can jump slightly on contract-roll days. |

**Verification status:** these tickers were confirmed to exist as Yahoo Finance quote pages (web
search of Yahoo's own pages, including the JSE ones being quoted in cents and `CPI` vs `CPIP`). They
were **not** fetched through `yfinance` while building, because the build sandbox blocks Yahoo. Step 5
of the setup is the real verification.

**Cents:** Yahoo quotes JSE equities in **cents (ZAc)**, e.g. Nedbank `26,734.00 ZAc`. Each equity has
`divisor = 100` in the config so the message shows Rand. If a share ever shows a value 100× too high
or low, that's the field to check.

### How "previous close" and "JSE closed" work

* Only **completed** sessions are used. Futures trade almost 24h, so today's partial bar is dropped.
* If the JSE didn't trade yesterday (weekend or SA public holiday, via the `holidays` package plus your
  `extra_jse_closed_dates`), the JSE lines collapse into one
  `JSE closed yesterday (Heritage Day); last session Wed 23 Sep` line instead of showing an old move
  as new. Brent and gold are unaffected.
* If a session that should exist is missing from Yahoo, the line shows its real date and
  `not updated` rather than a change.

## Failure behaviour

Every section is independent. A section that errors becomes `unavailable`; inside Markets and Rand a
single bad ticker or pair only affects its own line. The message is always sent. If **more than half**
of the sections fail, a warning line is added at the bottom. Each run logs per-section status and
timing, writes a table to the Actions run Summary, and emits a warning annotation for anything that
wasn't `ok`. Only a Telegram send failure (or missing secrets) turns the workflow red.

## Known limitations

* **Yahoo may throttle GitHub-hosted runners** (shared IPs). If it does, Markets shows
  `unavailable`, and the log says why.
* **Cron timing:** GitHub can start scheduled runs several minutes late, especially at the top of the
  hour. Expect the message around 07:00-07:15.
* **Idle repos:** GitHub pauses scheduled workflows on a *public* repo after 60 days without repo
  activity. Phase 2's committed state file will keep it active; until then, re-enable it in the
  Actions tab if that email arrives.
* **Test fixtures** for Open-Meteo and Frankfurter are hand-written from their docs, not recorded from
  live responses (see `tests/conftest.py`).

## Layout

```
.github/workflows/morning_brief.yml   schedule + manual trigger
config/settings.toml                  everything editable
brief/                                config, http, telegram, runner, calendar, sections/
jobs/morning_brief.py                 entrypoint
tests/                                pytest, fixture data only, no live calls
```
