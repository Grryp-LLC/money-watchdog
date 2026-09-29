# 🤠 Money Watchdog: the sheriff of your inbox

> A Grok Bot template that reads your email (read-only, always), catches the charges that sneak past you, puts a
> price on each one, helps you knock them off your list, and hangs a **MOST WANTED** poster on the worst offender.

*Sample posters are fictional demo data with a small "SAMPLE · DEMO DATA" stamp. Regenerate them with the commands in
[`samples/README.md`](samples/README.md).*

## What it does
1. **Watches your Gmail** for money trouble: declined cards and failed payments, upcoming charges and renewals,
   free trials about to convert, subscription price hikes, bills due, past-due notices, refunds owed, duplicate charges,
   bank and fraud alerts, and receipts for recurring charges.
2. **Classifies each one** by type, merchant, amount, date, urgency, and recurring vs. one-off, and **estimates potential
   savings** with a published formula table (cancel an unwanted sub, dodge a price hike, get a duplicate refunded, avoid a
   stated late fee). Every estimate comes from an amount written in the email and is labeled an estimate. If an email has
   no amount, no savings are claimed.
3. **Keeps a running ledger** of what it found and what you did (cancelled, refunded, kept, snoozed), dedupes reminder
   emails, and **only pings you when something needs action**. Quiet days send nothing.
4. **Turns findings into done.** After each report you tick the items you care about in a quick widget, then pick
   how: **add them to your to-do app** (Todoist, Google Tasks, Notion, Linear, TickTick via connector, or an
   Apple Reminders/calendar .ics, CSV, or checklist file), **"Fix it for me"** (it drafts the cancellation or dispute and
   walks you through the merchant's own cancel or billing page with you there, asking "yes, do it?" before each final
   click), or snooze/ignore. The ledger updates itself.
5. **Makes the fun part shareable:** a Wild-West **MOST WANTED** poster (charges listed as counts, "REWARD: $X/yr"
   bounty), a weekly **Bounty Board**, and a monthly **Rap Sheet**, rendered as PNGs at X-friendly sizes (1200×675 and
   1080×1350) with a suggested caption. Privacy-safe by default, with an optional **anonymous mode**.

## Why it's fun (and useful)
- Money admin is boring, and wanted posters aren't. The sheriff voice turns a creeping price hike into an outlaw with an alias
  ("The Price Creep") and a bounty, so it's something you *want* to deal with and post about.
- It's quiet unless something matters, so it doesn't turn into one more notification to ignore.
- The math is transparent. Ask "how did you get $216?" and it shows the quote and the formula.

## Screenshot list (rendered from `samples/specs/`, demo data)
| File | What |
|---|---|
| `wanted-streamopolis-1080x1350.png` / `-1200x675.png` | MOST WANTED: price hike + duplicate charge + silent renewal, $216/yr bounty |
| `wanted-ironhorse-1080x1350.png` / `-1200x675.png` | MOST WANTED: trial trap + buried fee, $529/yr bounty |
| `wanted-cloudcorral-anonymous-1080x1350.png` / `-1200x675.png` | **Anonymous mode**: merchant shown as "A Cloud Storage Plan" |
| `rapsheet-sep-2026-1080x1350.png` / `-1200x675.png` | Monthly Rap Sheet: stats, lineup, AT LARGE / CAUGHT / WATCHING / PARDONED stamps |
| `bountyboard-week-sep-21-1080x1350.png` / `-1200x675.png` | Weekly Bounty Board: pinned mini-posters on wood planks |
| `*-caption.txt` | Suggested X caption for each card |

## Setup for a new owner
1. Install the template in Grok Bot. The bot opens with its **money-watchdog-getting-started** conversation.
2. Connect **Gmail** when asked. That's the only required step. The bot only uses thread search and thread read.
3. It sweeps the last 60 days right away and shows your top items (with estimated savings) within minutes.
4. It then sends **one** settings message with defaults (8 AM daily check-in, posters on, merchant names shown, your
   favorite to-do app, optional names to keep off images). Reply "go" or change a line. It installs this kit on its own box (see "Install the kit")
   and creates three routines:
   - `daily-money-scan`: every day at your check-in time, silent unless something is actionable
   - `weekly-bounty-board`: Monday mornings, only if outlaws are at large
   - `monthly-rap-sheet`: the 1st of the month, with an offer of a WANTED poster for the month's most-wanted
5. Talk to it: "scan my inbox", "what's open?", "work the list", "keep TuneStable" (silences its monthly reminders), "I cancelled Streamopolis", "draft a cancellation for IronHorse",
   "make a wanted poster, anonymous", "go quiet".

## Privacy and safety guarantees (what the template enforces)
- **Read-only email.** The persona, every skill, and every routine prompt forbid send, reply, forward, Gmail drafts,
  labels, archive, trash, mark-read, unsubscribe, and filters. Drafts are delivered as text in chat.
- **Nothing happens without you.** It never follows links in emails, never buys anything or moves money, and never asks
  for or types passwords, codes, or card numbers. "Fix it for me" runs with you present, and every final click (cancel,
  submit, pay, save card) needs your explicit yes for that item. Drafts are handed to you; you send them.
- **Emails can't give orders.** Instructions inside emails are treated as evidence. Suspicious "verify your account"
  mail gets flagged as possible phishing.
- **Shareable images are scrubbed in code, not just by policy.** `poster/privacy.py` strips emails, URLs, card and account
  fragments, 4+ digit numbers (except years), phone numbers, and deny-listed names, and rounds every amount to whole
  dollars. A lint pass then **refuses to render** if anything slips through. Anonymous mode swaps merchants for categories.
- **No invented numbers.** Savings come only from amounts in the emails, via the table in `skills/score-savings`. If there's
  no amount, no bounty is claimed and no poster is made.
- **Nothing gets posted.** The bot hands you the PNG and a caption, and you decide whether to share.
- **No real brand logos by default.** Mugshots use line-art category icons. A logo shows up only if you supply one.

## 30-second demo script
| Time | On screen | Voiceover |
|---|---|---|
| 0–5s | Inbox full of receipts and "your plan is changing" emails | "Your inbox is where subscriptions go to hide." |
| 5–12s | Type "scan my inbox" → bot replies with 3 lines (act now / this week), each with amount, deadline, est. savings | "Money Watchdog reads it (read-only) and only barks when something needs you." |
| 12–18s | Widget: tick IronHorse + Streamopolis → "Add to Todoist" / "Fix it for me" → tasks land, cancel draft appears | "Tick what matters. It files the to-dos or drafts the breakup letter. You hit send, not the bot." |
| 18–26s | "make a wanted poster" → the MOST WANTED poster slides in: WANTED, merchant, COUNT 1–3, **REWARD $529/YR** | "Then it puts a bounty on the worst offender." |
| 26–30s | Rap Sheet card, then the anonymous-mode toggle | "Monthly rap sheet, privacy-safe, one tap to share. Money Watchdog: hands off my wallet." |

## Install the kit (what the bot runs; also works on any Linux/macOS box)
```bash
KIT=https://codeload.github.com/Grryp-LLC/money-watchdog/tar.gz/885f7260c303012e06f728092b65dc2e76cb06cb
mkdir -p ~/money-watchdog && curl -fsSL "$KIT" | tar xz --strip-components=1 -C ~/money-watchdog && bash ~/money-watchdog/install.sh
```
`install.sh` fetches the fonts from google/fonts at a pinned commit and checks their SHA-256, creates a Python venv with
Playwright and Pillow, uses the system Chrome/Chromium (or installs Playwright Chromium), and runs the self-test. Re-running
it is safe, and it never touches `ledger.json`.

The URL is pinned to commit `885f726` (kit v1.1: keep-silencing, honest per-year vs one-time bounties, `pick`/`export` for work-the-list).
The engine and poster code at that commit never change, so the bot always installs exactly what was reviewed.

```bash
cd ~/money-watchdog
.venv/bin/python poster/render.py poster/examples/wanted-demo.json --out out --sample
WATCHDOG_LEDGER=/tmp/l.json .venv/bin/python engine/ledger.py add engine/demo-findings.json && WATCHDOG_LEDGER=/tmp/l.json .venv/bin/python engine/ledger.py digest
bash tests/run_tests.sh
```

## Repo layout
```
bot-profile.md            name, title, description, full system prompt / persona
skills/<name>/SKILL.md    scan-inbox, score-savings, work-the-list, make-wanted-poster, monthly-rap-sheet, draft-cancellation, money-watchdog-getting-started
routines/ROUTINES.md      the three routines: cron, rationale, prompt
memories/                 portable memories for the template (profile + service log)
engine/ledger.py          ledger, dedupe, savings math, digest, widget options (pick), to-do export (csv/ics/md), poster specs
poster/render.py          HTML/CSS -> PNG renderer (Playwright + headless Chrome); privacy.py; icons.py
poster/fonts/             font license notices + fonts.lock (pinned URLs + SHA-256); install.sh fetches the files
poster/examples/          demo specs
samples/                  demo specs + captions (regenerate the PNGs with samples/README.md)
tests/run_tests.sh        end-to-end tests (dedupe, math, keep-silencing, quiet digest, pick/export, privacy gate, renders)
template/                 Grok Bot template manifest + publishing notes
install.sh                one-shot installer
```

## Licenses
Code: MIT (`LICENSE`). Fonts keep their own licenses: Rye, Sancreek and IM Fell under SIL OFL 1.1, and Special Elite under
Apache 2.0 (see `poster/fonts/README.md`). Merchant names in the samples (Streamopolis+, IronHorse Fitness, CloudCorral
Pro, Gazette Digital, Boxcar Meals, Prairie Power Co., TuneStable) are fictional.
