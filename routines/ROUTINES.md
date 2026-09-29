# Routines

All three are cron schedules in the owner's local timezone. Each prompt is written as an intent. Look up the Gmail tools
with MCP discovery at run time and don't hard-code tool schemas. Quiet rule: **a run with nothing actionable sends no
message.**

Why every day (7 days a week) for the daily scan: money deadlines (renewals, trial conversions, late fees) land on weekends
too, and the routine is silent unless something needs action. The weekly and monthly ones sit in normal morning hours.

## 1. daily-money-scan
- **Schedule:** `7 8 * * *` (8:07 AM owner-local, every day; the money-watchdog-getting-started skill adjusts it to their check-in time)
- **Prompt:**
  > Run the scan-inbox skill for the last 2 days of the owner's Gmail, read-only. Merge findings into the ledger
  > (dedupe), re-score with score-savings, and auto-resolve declines that have a later receipt. If anything is
  > actionable (act now or due within 10 days, or a new price hike, trial conversion, or refund owed), message the owner
  > with at most 6 short lines grouped by urgency, each with amount, deadline, estimated savings (labeled estimate),
  > and next step, then run work-the-list (pick widget of the open items, then how to handle them). If nothing is actionable, do not message the owner at all. Never send, reply, label, delete, draft, or
  > unsubscribe anything in Gmail. If Gmail auth fails on two runs in a row, pause this routine and tell the owner what to
  > reconnect.

## 2. weekly-bounty-board
- **Schedule:** `37 8 * * 1` (Mondays 8:37 AM owner-local)
- **Prompt:**
  > Using the ledger, list outlaws still at large (open or snoozed items). If there are none, do nothing and send no
  > message. Otherwise, if posters are on, build the weekly Bounty Board card with the monthly-rap-sheet skill (privacy
  > gate, anonymous mode if the owner prefers it) and send the owner both PNG sizes plus the suggested caption. If posters
  > are off, send a 3-line text recap. Never post anywhere.

## 3. monthly-rap-sheet
- **Schedule:** `17 9 1 * *` (1st of the month, 9:17 AM owner-local)
- **Prompt:**
  > Build last month's Rap Sheet from the ledger with the monthly-rap-sheet skill: stats, lineup, statuses, fine print
  > that bounties are estimates. Send the owner a 3-line private recap (spotted / collected / still at large, plus the
  > best next action) and, if posters are on, both PNG sizes plus the suggested caption. If the most-wanted merchant has
  > a dollar bounty, offer a WANTED poster (make-wanted-poster). If the month had no findings, send one line or nothing.
  > Never post anywhere.

## Owner controls
"go quiet" pauses all three, and "wake up" resumes them. "Change my check-in to 7" edits daily-money-scan (and moves the
weekly one to 30 minutes after it).
