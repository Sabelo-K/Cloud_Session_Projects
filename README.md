# SA Morning Brief

One Telegram message every morning (~07:00 SAST) with what matters to a Durban-based data analyst
following South African markets: weather, the rand, JSE and commodities, how your YouTube channels
are doing, SA economy headlines, and a "watch today" line for scheduled events.

Runs entirely on free tiers: GitHub Actions for scheduling, free public APIs for data, Telegram for
delivery. Secrets live only in GitHub Actions secrets.

> **Status: complete (Phase 3 of 3).** Everything in the example below, hardened (timeouts, circuit
> breaker, line budget, failure alert), plus an optional, off-by-default, *paid* headline summary.
> There is no YouTube Command Centre in this repo, so there is no `digest.py` to retire.

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
YouTube (public stats, subs rounded)
Durban Data Lab: 1,230 subs (+12) · 45,678 views (+312) · 42 videos
↳ How I track the JSE with Python · 1,204 views · 2d ago
SA economy
• Sarb ups repo rate to 7.25% as inflation risks build · Moneyweb
• Fuel price to fall in October, petrol down 32c · BusinessTech
Watch today: CPI inflation release (Stats SA)
```

Headlines and video titles are links. On a public-holiday morning the first line ends with
`· Public holiday: Heritage Day`. When the whole message would exceed `max_lines` (30), the blank
lines between sections are dropped; raise `max_lines` in `config/settings.toml` if you prefer spacing.

## Setup (do these in order)

1. **Create a Telegram bot.** In Telegram, message [@BotFather](https://t.me/BotFather), send
   `/newbot`, follow the prompts, and copy the **bot token**.
2. **Get your chat ID.** Send your new bot any message (e.g. `/start`; a bot can't message you until
   you've messaged it). Open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser and copy
   the number in `"chat":{"id":...}`. (Alternative: message [@userinfobot](https://t.me/userinfobot).)
3. **Create a YouTube API key.** [Google Cloud Console](https://console.cloud.google.com) → create a
   project → *APIs & Services → Library* → enable **YouTube Data API v3** → *Credentials → Create
   credentials → API key*. (Optional but sensible: restrict the key to that one API.) The job uses
   about 4 of the 10,000 free daily quota units.
4. **Find your channel IDs** and put them in `config/settings.toml` under `[[youtube.channels]]`
   (uncomment the examples). An ID starts with `UC` and is 24 characters long: open the channel →
   *About → Share channel → Copy channel ID*. **An @handle will not work.**
5. **Get this code onto the repository's default branch.** GitHub only lists a workflow, and only runs
   its schedule, once it's on the default branch.
6. **Add three repository secrets:** *Settings → Secrets and variables → Actions → New repository
   secret*: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `YOUTUBE_API_KEY`.
7. **Dry-run to verify every data source.** *Actions → Morning Brief → Run workflow*, tick
   **Dry run**. Open the run and check:
   * the log prints the message; the run's **Summary** lists each section as `ok` / `partial` /
     `failed` with the reason;
   * every ticker shows a number, not `unavailable`;
   * each feed logs `feed=<name> ok items=N newest=...` or `FAILED <reason>`. **Fix any failed feed**
     (see *RSS feeds* below).
   A dry run never sends to Telegram and never saves or commits anything.
8. **Send a real one.** Run the workflow again with Dry run unticked.
9. **Done.** It now runs daily at 05:00 UTC (07:00 SAST). The first real run saves the first YouTube
   snapshot, so day-over-day changes appear from the *second* morning (the first shows
   `(first snapshot)`).

## Run locally

```bash
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
pytest                                   # no network needed
cp .env.example .env                     # then fill in the values
python -m jobs.morning_brief --dry-run   # print only, no Telegram needed
python -m jobs.morning_brief             # send for real
```

`LOG_LEVEL=DEBUG` shows the raw values fetched per source. `--date 2026-09-25` pretends it's that
morning, to check holiday/market-closed behaviour (live weather/FX still describe the real today, so
those sections may fail for other dates). A local non-dry run writes `data/youtube_history.json`.

## Configuration

* [`config/settings.toml`](config/settings.toml): location, currency pairs, tickers, YouTube channels
  and data source, RSS feeds and keywords, the line limit, and an `enabled = false` switch per section.
* [`config/events.toml`](config/events.toml): your "watch today" dates. One `[[event]]` per date; the
  text shows on that morning only. Nothing shows on other days.

## Data sources

| Section | Source | Key | Verified while building? |
|---|---|---|---|
| Weather | [Open-Meteo](https://open-meteo.com), Durban (-29.86, 31.03) | No | Yes, live |
| Rand | [Frankfurter](https://frankfurter.dev): ECB rates, **published once per business day**, so Monday's brief shows Friday's. The heading always states the date. | No | Yes, live |
| Markets | Yahoo Finance via [`yfinance`](https://github.com/ranaroussi/yfinance): **unofficial**, can break or rate-limit | No | Yes, live: all 8 tickers return data |
| YouTube | [YouTube Data API v3](https://developers.google.com/youtube/v3), public stats | API key | Auth method and error responses **verified live**; success responses from docs |
| Headlines | RSS feeds, see below | No | Yes, live (4 feeds work) |
| Watch today | `config/events.toml` (yours) | n/a | n/a |
| Holidays | the [`holidays`](https://pypi.org/project/holidays/) package (ZA) | n/a | Yes (incl. 4 Nov 2026 local-election holiday) |

### Yahoo tickers

| Line | Ticker | Notes |
|---|---|---|
| JSE Top 40 | `^J200.JO` | Index points |
| Standard Bank / FirstRand / Absa / Nedbank | `SBK.JO` / `FSR.JO` / `ABG.JO` / `NED.JO` | |
| Capitec | `CPI.JO` | Ordinary shares. **Not** `CPIP.JO`, the preference share. |
| Brent crude | `BZ=F` | Front-month future, USD/bbl |
| Gold | `GC=F` | COMEX front-month future, USD/oz; % change can jump on contract-roll days |

Yahoo quotes JSE equities in **cents (ZAc)** (e.g. Nedbank `26,734.00 ZAc`), so each equity has
`divisor = 100` in the config and the message shows Rand. Only *completed* sessions are used. If the
JSE didn't trade yesterday (weekend, public holiday, or a date in `extra_jse_closed_dates`), its lines
collapse into one `JSE closed yesterday (Heritage Day); last session Wed 23 Sep` line instead of
showing an old move as new.

### RSS feeds

Tested live from GitHub's runners on 29 Sep 2026:

| Outlet | Result |
|---|---|
| Moneyweb `https://www.moneyweb.co.za/feed/` | Works |
| Daily Maverick `https://www.dailymaverick.co.za/dmrss/` | Works. Whole-site feed, so `keyword_only` (keyword must be in the title) |
| The Citizen (business) `https://www.citizen.co.za/business/feed/` | Works, `keyword_only` |
| Google News search (Reserve Bank / repo rate / SA economy) | Works. **Stands in for a SARB feed**: it surfaces Reserve Bank stories from many outlets. Links go via news.google.com and redirect to the article |
| BusinessTech, Daily Investor, MyBroadband | **Blocked (HTTP 403)** from GitHub's runners, even with a browser User-Agent. Removed |
| Business Day | Disabled. Copy the Economy feed URL from https://www.businessday.co.za/information/rss-feeds/ into `settings.toml` if you want it |
| SARB | No official feed URL could be found; see Google News above and `events.toml` for MPC dates |

A dead feed only costs you its own headlines: it's logged as `FAILED <reason>`, flagged as a warning on
the run, and the rest still work. Ranking is by keyword hits (title counts triple vs summary), then
recency; near-duplicate stories are collapsed, at most 2 per outlet, items older than 48h are ignored.
`exclude_phrases` stops place names like "East Rand" matching `rand`. Keyword matching is blunt:
occasionally an off-topic headline gets through (e.g. a "military budget" story matches `budget`), so
trim the `keywords` list if that annoys you. Only headline + link are shown; article text is never used.

### YouTube

Public stats only, via the Data API and an API key (no OAuth). Per channel: subscribers, total views,
video count, and the latest upload (title, link, views, age). Change vs the previous day comes from
`data/youtube_history.json`, which the workflow commits after each real run (120 days kept).

* **Subscriber counts are rounded** by YouTube to 3 significant figures, so on bigger channels a
  small daily change may not show at all. Counts under 1,000 are exact. Some channels hide the count.
* The section is capped at 7 lines however many channels you list (2 lines each up to 3 channels, then 1).
* **Switching to the YouTube Command Centre later** is a config change: the renderer only consumes
  source-neutral `ChannelReport` objects (`brief/youtube/models.py`). A Supabase source is one new
  class registered in `brief/youtube/__init__.py`, then `source = "supabase"` in `settings.toml`.
* If your default branch is **protected**, the history commit will be refused; allow GitHub Actions to
  push, or tell me and we'll move the history to its own branch.

## Optional: a plain-English briefing instead of headline links (off by default, paid)

If you don't have time to click and read, this replaces the **SA economy** link list with 3-4 plain
sentences on what is happening (rates, rand, fuel, jobs, power, budget...), written by Claude from the
day's headlines. It is the only feature that isn't free: you need your own Anthropic API key with
credit, and it costs a few cents a month at the default model.

To turn it on:
1. Create an API key at https://console.anthropic.com and add credit.
2. Add it as a repository secret named `ANTHROPIC_API_KEY`.
3. In `config/settings.toml` set `[summary] enabled = true`.

Settings under `[summary]`: `model` (default `claude-opus-5-5`; a smaller model is cheaper),
`send_excerpts` (headline titles plus each outlet's short RSS excerpt, or `false` for titles only), and
`links` (how many source links to keep under the briefing; default 0).

What is sent to Anthropic: headline titles and, unless you turn it off, the ~300-character excerpt each
outlet publishes in its RSS feed. No links, and nothing about you. The model is told to use only that
material and not to follow instructions inside it. It can still occasionally paraphrase badly, which is
why `links` exists if you want to spot-check. If the key is missing or anything fails (API error,
refusal, empty answer), you simply get the normal headline list for that day and the problem is
logged. The workflow installs the `anthropic` package only if the secret exists. The AI updates
section never uses this.

## Failure behaviour

Every section is independent. A section that errors becomes `unavailable`; a single bad ticker, currency
pair, feed or channel only affects itself. The message is always sent. If **more than half** of the
sections fail, a warning line is added at the bottom.

Hardening beyond that:

* **Timeouts:** a section that takes over `section_timeout_seconds` (120) is abandoned so the message
  still goes out on time.
* **Yahoo circuit breaker:** after 3 failed tickers in a row the rest are skipped (Yahoo tends to fail
  all-or-nothing), and Markets never spends over 60s. A total Yahoo outage costs ~15s, not ~45s.
* **Line budget:** if the message exceeds `max_lines`, blank separators go first, then headlines beyond
  the third. The warning line is never trimmed.
* **Stale data:** ECB rates older than 4 days are flagged in the Rand heading.
* **Last resorts:** if building the message crashes, a short "could not be built" notice is still sent;
  a failure writing the Actions summary can't stop the send.
* **Job-level alert:** if the workflow itself dies before the script can send (e.g. a dependency
  install fails), a fallback step messages you the run link. A run GitHub never starts (or drops) can't
  be detected; a missing 07:00 message is the signal. Each run logs per-section status and timing,
writes a table to the Actions run Summary, and emits a warning annotation for anything not `ok`. Only a
Telegram send failure (or missing Telegram secrets) turns the workflow red. Sections with nothing to
show (no event today, no channels configured) are silent in the message but still flagged in the log if
misconfigured.

## Known limitations

* **Yahoo may throttle GitHub-hosted runners** (shared IPs). If it does, Markets shows `unavailable` and
  the log says why.
* **Cron timing:** GitHub can start scheduled runs several minutes late; expect ~07:00-07:15.
* **Idle repos:** GitHub pauses scheduled workflows on a *public* repo after 60 days without activity.
  The daily history commit should count as activity; if you get that email anyway, re-enable the
  workflow in the Actions tab.
* **Test fixtures** for Open-Meteo, Frankfurter, the YouTube success responses and the RSS feeds are
  hand-written from documentation, not recorded (see `tests/conftest.py`). The two YouTube *error*
  fixtures are real recorded responses.

## Layout

```
.github/workflows/morning_brief.yml   schedule + manual trigger + history commit
config/settings.toml, events.toml     everything editable
brief/                                config, http, telegram, runner, header, rss, calendar
brief/sections/                       weather, fx, markets, youtube, headlines, watch
brief/youtube/                        source-neutral models, Data API source, JSON history
jobs/morning_brief.py                 entrypoint
tests/                                pytest (~240), fixture data only, no live calls; also run on every push
brief/summary.py                      optional paid SA economy briefing (off by default)
```

## F1 analysis (work in progress)

A separate app in `f1/`: lap times, race pace, tyre stints and degradation, championship progression, and qualifying/telemetry comparison for any race since 2018.
Data: FastF1 (laps) and Jolpica (schedule). Run: `pip install -r requirements-f1.txt && python -m streamlit run f1/app.py`.
Pace maths lives in `f1/pace.py` and is unit-tested with synthetic laps (`tests/test_f1_pace.py`).
