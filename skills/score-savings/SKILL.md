---
name: score-savings
description: >-
  Transparent math for "potential money saved" on each finding. Use whenever a finding is scored, a poster bounty is set,
  or the owner asks "how did you get that number?". Estimates come only from amounts in the emails.
---
# Score savings (transparent, conservative, always labeled "estimate")

Principles: (1) Every input number is quoted from an email. (2) No amount means no savings claimed, so write "no $
claimed". (3) Always show the formula on request. (4) Say "estimate" or "est." wherever a number is shown. (5) "If
cancelled" savings assume the owner decides they don't need it. We can't know usage, so we never claim they don't use
it.

Periods per year: weekly 52, monthly 12, quarterly 4, semiannual 2, annual/season 1, once 0.

| Finding type | Savings kind | Formula | Example basis line |
|---|---|---|---|
| trial_ending (converts to paid) | cancel_recurring | amount × periods | "$40/mo × 12 if cancelled before trial ends" |
| renewal / upcoming_charge (recurring) | cancel_recurring | amount × periods | "$125/yr × 1 if cancelled" |
| price_increase | cancel_recurring (+ hike shown) | cancel = new × periods; hike = (new − old) × periods | "$18/mo × 12 if cancelled (hike alone: $30/yr)" |
| receipt_recurring | review_recurring (counts only after the owner says it's unused) | amount × periods | "$20/mo × 12 if unused" |
| duplicate_charge | refund (one-time) | duplicate amount | "$18 duplicate refund" |
| refund_owed | refund (one-time) | refund amount | "$60 refund owed" |
| fraud_alert with amount | dispute (one-time) | charge amount | "$89 if the charge is unauthorized" |
| bill_due / past_due / declined with a stated late or failed-payment fee | avoid_fee (one-time) | stated fee | "$25 late fee avoided" |
| bill_due / past_due / declined with no fee stated | none | 0 | "no fee stated, so no savings claimed" |

Rules:
- The bill amount itself is **never** "savings". Paying a bill on time only saves the stated fee.
- One merchant's bounty = recurring part (sum of cancel_recurring per-year values) + one-time part (refunds, disputes,
  avoided fees) from its open findings. Always keep the two parts separate when shown: "~$24/yr + $10 one-time", never
  "$34/yr". One-time money is never annualized.
- Price hikes: the conservative figure is the hike delta. Use the full cancel value only with the "if cancelled"
  label.
- Rounding: keep cents in the ledger. Show whole dollars ("~$216/yr") everywhere else. Posters use whole dollars
  only.
- Currency: don't mix currencies. Convert only if the email itself gives both, otherwise score each currency
  separately.
- "Collected" (money the owner actually saved) counts only items the owner marked handled with action
  cancelled/refunded/disputed/downgraded/paid-before-fee. It's still labeled "est." because it's projected from the
  emails, not a bank statement.

If the kit is installed, `engine/ledger.py` implements exactly this table (`score()`), so use it rather than
re-doing the math by hand.

When asked "how did you get $X?", answer with the quote, the formula, and the result:
"Streamopolis+ email: 'your plan will change to $17.99/month' (was $15.49) → cancel: 17.99 × 12 = ~$216/yr; hike alone: (17.99 − 15.49) × 12 = ~$30/yr. Estimates."
