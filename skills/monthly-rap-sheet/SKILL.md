---
name: monthly-rap-sheet
description: >-
  Monthly "Rap Sheet" summary card and weekly "Bounty Board" card (PNG, 1200x675 + 1080x1350) built from the ledger,
  plus a short private recap and a suggested X caption. Use in the weekly and monthly routines or when the owner asks
  for a rap sheet, bounty board, or recap.
---
# Monthly Rap Sheet and weekly Bounty Board

## Rap Sheet (monthly, for the previous calendar month)
1. Pull every ledger item first seen, charged, or due in that month. With the kit: `ledger.py rapsheet --month YYYY-MM
   --out rap.json`.
2. Rows (the card shows up to 7 portrait / 5 landscape, highest bounty first): merchant, one-line crime, bounty
   (`/yr` for recurring, `once` for one-time, `—` if no amount), and status stamp:
   - **AT LARGE**: still open
   - **CAUGHT**: owner handled it (cancelled / refunded / disputed / downgraded / paid before the fee)
   - **WATCHING**: snoozed
   - **PARDONED**: owner chose to keep it, or dismissed it
3. Stat boxes: *Outlaws spotted* (count of findings), *Still at large* (sum of open recurring bounties, est. /yr),
   *Bounties collected* (sum of CAUGHT bounties, est.). The fine print "Bounties are estimates from amounts in the
   emails…" stays on the card.
4. The same privacy gate as make-wanted-poster applies (merchant names and whole dollars only; anonymous mode
   available).
5. Render: `render.py rap.json --out ~/money-watchdog/out`. Look at both PNGs yourself, then send them with:
   - a 3-line private recap: spotted / collected / still at large, plus the single best next action;
   - the suggested caption from `*-caption.txt` (the owner decides whether to post).
6. If the month's most-wanted merchant has a dollar bounty, also offer a WANTED poster for it (make-wanted-poster).
7. If the month had zero findings, send one line ("Quiet month in town. No outlaws spotted.") and no card, unless the
   owner asks for one.

## Bounty Board (weekly)
- Shows up to 3 open outlaws as pinned mini-posters on a wood board, with total bounty on the board (est. /yr). The
  portrait version adds a "Sheriff's Notice" card with the count and total.
- With the kit: `ledger.py board --week-of YYYY-MM-DD --out board.json`, then `render.py board.json`.
- Send only if at least one outlaw is at large. Otherwise stay silent.

## Honesty rules
- Never inflate: collected ≠ at large, and one-time money is never annualized.
- Never add merchants that aren't in the ledger, and never carry numbers over from demo data.
- Never post, schedule, or send the image anywhere except to the owner.
