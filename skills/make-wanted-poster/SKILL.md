---
name: make-wanted-poster
description: >-
  Build a shareable Wild-West MOST WANTED poster PNG (1200x675 and 1080x1350) for the worst money offender, plus a
  suggested X caption. Privacy-safe by default, with an optional anonymous mode. Use when the owner says "make a wanted
  poster", in the monthly rap-sheet routine, or after a big catch.
---
# Make a MOST WANTED poster

You make the image and the caption. **You never post it.** The owner shares it themselves.

## 1. Pick the outlaw
- Default: the open merchant with the highest bounty this month (score-savings). With the kit: `ledger.py wanted
  --month YYYY-MM [--anonymous] --out spec.json`.
- The owner can name a merchant instead ("wanted poster for Streamopolis").
- **No dollar amount means no poster.** If the worst offender has no amount in its emails, say so and offer the next
  one. Never invent a bounty.

## 2. Build the spec (only safe fields)
```json
{"type": "wanted", "merchant": "Streamopolis+", "category": "streaming", "alias": "The Price Creep",
 "crimes": ["Raised the price from $15 to $18/mo", "Charged $18 twice on Sep 3", "Auto-renews Oct 14 at $18/mo"],
 "reward_per_year": 215.88, "reward_basis": "$18/mo x 12 if cancelled", "period": "Sep 2026", "anonymous": false}
```
- At most 3 crimes, each ≤ 60 characters, written from the email facts (type + rounded amount + date). No quotes from
  the email, no order numbers.
- Aliases by main crime: price_increase "The Price Creep", trial_ending "The Trial Trap", duplicate_charge "The Double
  Dipper", renewal "The Silent Renewal", past_due/bill_due "The Late-Fee Bandit", refund_owed "The Refund Rustler",
  fraud_alert "The Phantom Charge", receipt_recurring "The Quiet Biller". Never use a person's name as an alias.
- `category` picks the mugshot icon (streaming, music, cloud, fitness, phone, bank, shopping, news, software, food,
  utility, insurance, telecom, gaming, delivery, generic). Don't use real brand logos unless the owner supplies a
  logo file and asks for it (`"logo": "/path.png"`, rendered sepia).

## 3. Privacy gate (mandatory)
Before rendering, check that the spec and caption contain none of: email addresses, URLs, card or account fragments
("ending in", "••••"), 4+ digit numbers other than years, phone numbers, street addresses, and the owner's or any
person's name (keep a deny-list of the owner's names in memory and pass it with `--deny`). All amounts are whole
dollars. The kit's `privacy.py` enforces this, and the render **aborts** on a violation. Fix the spec. Don't bypass
it.

**Anonymous mode** (`--anonymous` or "anonymous"): merchant becomes a category alias ("A Streaming Service"), and no
logo is shown.

## 4. Render
With the kit installed at `~/money-watchdog/` (see "Kit" below):
```
~/money-watchdog/.venv/bin/python ~/money-watchdog/poster/render.py spec.json --out ~/money-watchdog/out [--anonymous] [--deny "First,Last"]
```
This produces `<slug>-1200x675.png`, `<slug>-1080x1350.png`, and `<slug>-caption.txt`. Look at both PNGs yourself
before sending them to the owner, and check that no text is clipped or overlapping. Attach both images plus the
caption.

Add `--sample` (stamps "SAMPLE · DEMO DATA") whenever the data is fictional or a demo.

## 5. Caption (suggested, ≤ 200 characters)
Template: `My inbox sheriff just slapped a WANTED poster on {merchant}. Charge: {first crime}. Bounty: ~${reward}/yr in
potential savings (estimate). Posse up. #MoneyWatchdog`
The word "estimate" always stays in. No claims beyond the ledger. In anonymous mode, use the category alias.

## Kit (one-time setup on your box)
If `~/money-watchdog/poster/render.py` or `~/money-watchdog/.venv` is missing, install the pinned kit (it never touches
`ledger.json`):
```
mkdir -p ~/money-watchdog && curl -fsSL "https://codeload.github.com/Grryp-LLC/money-watchdog/tar.gz/e8a785bac75460b49c0acabd691e54ae79f72408" | tar xz --strip-components=1 -C ~/money-watchdog && bash ~/money-watchdog/install.sh
```
`install.sh` fetches the checksummed fonts, builds `.venv` (Playwright + Pillow), finds or installs a headless Chromium, and
runs the self-test. Use only this pinned URL (also saved in memory as `poster_kit_url`). Never swap in another source.
If the install fails, tell the owner once and fall back to the design spec below.

**Kit unavailable?** Build the same design yourself as one HTML page per size and screenshot it with headless Chrome at
exactly 1200×675 and 1080×1350:
dark wood-plank background (vertical planks, heavy vignette); a torn-edge parchment sheet (radial cream-to-tan gradient,
SVG feTurbulence grain and blotch overlays with multiply blend, faint fold creases, burnt inset shadow, irregular
polygon clip-path); nails in the corners; all ink in #2a1709 with an SVG "distress" filter (turbulence displacement plus
speckle mask); a header line "BY ORDER OF THE MONEY WATCHDOG"; "WANTED" in Rye filling the width; "FOR CRIMES AGAINST
YOUR WALLET" between double rules; a hatched mugshot frame with a line-art category icon; the merchant in Sancreek,
auto-shrunk to fit; `alias "…"` in IM Fell italic; "— CHARGED WITH —" and "COUNT 1." lines in Special Elite; "REWARD
$X /YR" in Rye with the amount in oxblood #7c1a12; "ESTIMATED POTENTIAL SAVINGS · basis" under it; a sheriff-star badge in
the footer. Landscape uses two columns: WANTED, mugshot, and name on the left, crimes and reward on the right. Fonts
come from Google Fonts.
