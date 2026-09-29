---
name: draft-cancellation
description: >-
  Draft (never send) a cancellation, downgrade, refund, duplicate-charge dispute, late-fee waiver, or price-hike
  pushback message for the owner to review and send themselves. Use when the owner asks to cancel, dispute, or get
  money back from a merchant in the ledger.
---
# Draft a cancellation or dispute (owner sends it)

**Hard rule:** you produce text in chat, or a file on your box. You never create a Gmail draft, never send, and
never submit a merchant's web form. The owner copies it and sends it.

## Steps
1. Find the ledger item(s) for the merchant. Re-read the source email (read-only) for exact facts: the plan name,
   amount, dates, and what the email says about how to cancel (link, settings page, phone, "reply to this email").
2. Tell the owner the **fastest real path** first. Most subscriptions cancel in account settings, and an email is only
   needed when the merchant requires one, for disputes, or as a paper trail. For card disputes, say they can also
   contact their card issuer.
3. Draft the message:
   - **To:** the support address named in the merchant's own email. If none is named, write "[merchant support
     address from their website]". Never guess an address.
   - **Subject:** short and specific.
   - **Body:** 4–8 sentences, polite and firm: who they are (the "account email on file" placeholder, never pasted from
     the ledger if the owner hasn't given it), what they want (cancel effective immediately / refund $X duplicate from
     <date> / waive the $Y late fee / keep the old price), the facts (dates, amounts from the email), and a request for
     written confirmation.
   - Placeholders in [brackets] for anything you don't know (account ID, last 4). Don't fill them from email metadata.
4. Offer variants: "firmer", "shorter", "chat script" (for live chat), "phone script" (bullets).
5. After the owner says they sent it or finished, mark the ledger item handled with the matching action (cancelled /
   disputed / refunded / downgraded) and schedule nothing. The next daily scan will spot the confirmation email.

## Templates
**Cancel before renewal**
Subject: Please cancel my [plan] before the [date] renewal
Hello, please cancel my [plan] subscription effective immediately and make sure I'm not charged the [amount] renewal on
[date]. Please confirm the cancellation in writing. Thank you, [name]

**Duplicate charge**
Subject: Duplicate charge on [date]: refund request
Hello, I was charged [amount] twice on [date] for the same [plan/order]. Please refund the duplicate charge to my original
payment method and confirm by email. Thank you, [name]

**Price hike pushback / retention**
Subject: Price change on my [plan]
Hello, I got notice that my [plan] is going from [old] to [new]. I'd like to keep my current rate or move to a cheaper plan.
Otherwise, please cancel before [date]. Please let me know which options are available. Thanks, [name]

**Late-fee waiver**
Subject: Request to waive late fee
Hello, I've been a customer since [year] and missed the [date] due date. I've now paid [amount]. As a courtesy, would you
waive the [fee] late fee? Thank you, [name]
