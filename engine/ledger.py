#!/usr/bin/env python3
"""Money Watchdog ledger + transparent savings math.

The bot (LLM) reads email and extracts structured findings; this script owns everything that must be
deterministic and auditable: dedupe, savings math, the running ledger, what deserves a ping, and the
poster specs fed to poster/render.py.

  ledger.py add findings.json            merge new findings (dedupe), print what is new + actionable
  ledger.py set <id> --status handled --action cancelled [--note "..."]   (--action kept silences repeats)
  ledger.py digest [--today YYYY-MM-DD]  actionable open items, or the single word QUIET
  ledger.py show [--all]                 human-readable ledger table
  ledger.py wanted --month YYYY-MM [--anonymous] [--out spec.json]
  ledger.py rapsheet --month YYYY-MM [--anonymous] [--out spec.json]
  ledger.py board --week-of YYYY-MM-DD [--anonymous] [--out spec.json]
  ledger.py pick [--limit 5] [--offset 0] [--today YYYY-MM-DD]   widget-ready options for work-the-list
  ledger.py export <id>... --format csv|ics|md --out FILE         to-do file (Todoist CSV / calendar .ics / checklist)

Ledger path: $WATCHDOG_LEDGER or ~/money-watchdog/ledger.json. The ledger is private (it holds thread ids and
short evidence quotes); poster specs built from it contain only merchant, category, rounded amounts,
dates and plain-language charges.
"""
import argparse, datetime as dt, hashlib, json, os, re, sys
from pathlib import Path

LEDGER = Path(os.environ.get("WATCHDOG_LEDGER", str(Path.home() / "money-watchdog" / "ledger.json")))
PERIODS = {"weekly": 52, "monthly": 12, "quarterly": 4, "semiannual": 2, "annual": 1, "yearly": 1, "once": 0}
UNIT = {"weekly": "wk", "monthly": "mo", "quarterly": "qtr", "semiannual": "6mo", "annual": "yr", "yearly": "yr"}
TYPES = ["declined", "upcoming_charge", "renewal", "trial_ending", "price_increase", "bill_due", "past_due",
         "refund_owed", "duplicate_charge", "fraud_alert", "receipt_recurring"]
ALIAS = {"price_increase": "The Price Creep", "trial_ending": "The Trial Trap", "duplicate_charge": "The Double Dipper",
         "renewal": "The Silent Renewal", "upcoming_charge": "The Silent Renewal", "past_due": "The Late-Fee Bandit",
         "bill_due": "The Late-Fee Bandit", "refund_owed": "The Refund Rustler", "fraud_alert": "The Phantom Charge",
         "declined": "The Card Wrangler", "receipt_recurring": "The Quiet Biller"}
URGENCY_RANK = {"act_now": 0, "this_week": 1, "fyi": 2}

def m(x):
    return f"${round(float(x)):,}"

def load():
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else {"version": 1, "items": []}

def save(led):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, indent=2, sort_keys=False))

def norm_merchant(s):
    s = re.sub(r"(?i)\b(inc|llc|ltd|corp|co|the|billing|payments?|team|support|no-?reply)\b\.?", "", s or "")
    return re.sub(r"[^a-z0-9+]", "", s.lower())

def key(f):
    """Dedupe key: same merchant + type + amount + due/billing month = same finding (reminder emails repeat)."""
    when = (f.get("due_date") or f.get("charge_date") or f.get("email_date") or "")[:7]
    amt = f"{float(f.get('amount') or 0):.2f}"
    return hashlib.sha1(f"{norm_merchant(f['merchant'])}|{f['type']}|{amt}|{when}".encode()).hexdigest()[:10]

# ------------------------------------------------------------------ savings math (documented in score-savings skill)
def score(f):
    t, amt = f["type"], float(f.get("amount") or 0)
    cad = (f.get("cadence") or ("once" if not f.get("recurring") else "monthly")).lower()
    per = PERIODS.get(cad, 0)
    fee = float(f.get("late_fee") or 0)
    old = float(f.get("old_amount") or 0)
    s = {"per_year": 0.0, "one_time": 0.0, "kind": "none", "basis": "", "formula": ""}
    if t in ("trial_ending", "renewal", "upcoming_charge", "receipt_recurring") and per and amt:
        s.update(per_year=amt * per, kind="cancel_recurring",
                 basis=f"{m(amt)}/{UNIT.get(cad, cad)} x {per} if cancelled",
                 formula=f"{amt:.2f} x {per}")
        if t == "receipt_recurring":
            s["kind"] = "review_recurring"  # counted only if the user decides it is unused
    elif t == "price_increase" and amt and old and per:
        s.update(per_year=amt * per, kind="cancel_recurring", hike_per_year=(amt - old) * per,
                 basis=f"{m(amt)}/{UNIT.get(cad, cad)} x {per} if cancelled (hike alone: {m((amt - old) * per)}/yr)",
                 formula=f"cancel {amt:.2f} x {per}; hike ({amt:.2f}-{old:.2f}) x {per}")
    elif t == "duplicate_charge" and amt:
        s.update(one_time=amt, kind="refund", basis=f"{m(amt)} duplicate refund", formula=f"{amt:.2f}")
    elif t == "refund_owed" and amt:
        s.update(one_time=amt, kind="refund", basis=f"{m(amt)} refund owed", formula=f"{amt:.2f}")
    elif t == "fraud_alert" and amt:
        s.update(one_time=amt, kind="dispute", basis=f"{m(amt)} if the charge is unauthorized", formula=f"{amt:.2f}")
    elif t in ("bill_due", "past_due", "declined") and fee:
        s.update(one_time=fee, kind="avoid_fee", basis=f"{m(fee)} late/failed-payment fee avoided", formula=f"{fee:.2f}")
    elif t in ("bill_due", "past_due", "declined"):
        s.update(kind="none", basis="no fee stated in the email, so no savings claimed")
    s["estimate"] = True
    return s

def urgency(f, today):
    if f.get("urgency") in URGENCY_RANK:
        return f["urgency"]
    t = f["type"]
    if t in ("declined", "past_due", "fraud_alert", "duplicate_charge"):
        return "act_now"
    d = f.get("due_date")
    if d:
        days = (dt.date.fromisoformat(d[:10]) - today).days
        if days <= 3: return "act_now"
        if days <= 10: return "this_week"
    return "fyi"

def actionable(it, today):
    if it["status"] != "open": return False
    if it.get("snooze_until") and it["snooze_until"] > today.isoformat(): return False
    if it["type"] == "receipt_recurring" and not it.get("changed"): return False  # routine receipts stay quiet
    return urgency(it, today) in ("act_now", "this_week") or it["type"] in ("price_increase", "trial_ending", "refund_owed")

# ------------------------------------------------------------------ commands
def cmd_add(a):
    led = load(); today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    found = json.loads(Path(a.findings).read_text())
    found = found.get("findings", found) if isinstance(found, dict) else found
    by_id = {it["id"]: it for it in led["items"]}
    new, updated = [], []
    for f in found:
        if f.get("type") not in TYPES:
            print(f"skip (unknown type): {f.get('type')}", file=sys.stderr); continue
        k = key(f)
        if k in by_id:
            it = by_id[k]
            it["seen_count"] = it.get("seen_count", 1) + 1
            it["last_seen"] = today.isoformat()
            for tid in f.get("thread_ids", [f.get("thread_id")]):
                if tid and tid not in it["thread_ids"]: it["thread_ids"].append(tid)
            updated.append(it); continue
        it = dict(f)
        it.update(id=k, first_seen=today.isoformat(), last_seen=today.isoformat(), seen_count=1,
                  status="open", action=None, history=[],
                  thread_ids=[x for x in f.get("thread_ids", [f.get("thread_id")]) if x])
        it.pop("thread_id", None)
        it["savings"] = score(it)
        it["urgency"] = urgency(it, today)
        prev = kept_before(led, it)
        if prev:  # owner already said "keep it" for this merchant/type/amount: record it, stay quiet
            it.update(status="dismissed", action="kept")
            it["history"].append({"at": today.isoformat(), "from": "open", "to": "dismissed", "action": "kept",
                                  "note": f"auto: owner kept this before ({prev['id']})"})
        led["items"].append(it); by_id[k] = it; new.append(it)
    save(led)
    print(json.dumps({"new": len(new), "repeat_sightings": len(updated),
                      "new_actionable": [brief(i) for i in new if actionable(i, today)]}, indent=2))

def kept_before(led, it):
    """Owner said "keep X" earlier for the same merchant + type + amount -> next month's reminder is not news.
    A different amount (e.g. a price change) is news again, so it still alerts."""
    for x in led["items"]:
        if (x.get("action") == "kept" and x["type"] == it["type"]
                and norm_merchant(x["merchant"]) == norm_merchant(it["merchant"])
                and abs(float(x.get("amount") or 0) - float(it.get("amount") or 0)) < 0.005):
            return x
    return None

def brief(i):
    s = i["savings"]
    val = (f"~{m(s['per_year'])}/yr" + (" if unused" if s["kind"] == "review_recurring" else "") if s["per_year"] else f"~{m(s['one_time'])} once" if s["one_time"] else "no $ claimed")
    return {"id": i["id"], "type": i["type"], "merchant": i["merchant"], "amount": i.get("amount"),
            "due": i.get("due_date"), "urgency": i.get("urgency"), "estimate": val, "basis": s["basis"]}

def cmd_set(a):
    led = load()
    it = next((x for x in led["items"] if x["id"] == a.id), None)
    if not it: sys.exit(f"no item {a.id}")
    it["history"].append({"at": dt.datetime.now().isoformat(timespec="minutes"), "from": it["status"], "to": a.status,
                          "action": a.action, "note": a.note})
    it["status"], it["action"] = a.status, a.action or it.get("action")
    if a.snooze_until: it["snooze_until"] = a.snooze_until
    if a.unused and it["savings"]["kind"] == "review_recurring": it["savings"]["kind"] = "cancel_recurring"
    save(led); print(json.dumps(brief(it), indent=2))

def cmd_digest(a):
    led = load(); today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    for it in led["items"]:
        it["urgency"] = urgency({**it, "urgency": None}, today) if it["status"] == "open" else it.get("urgency")
    items = sorted([i for i in led["items"] if actionable(i, today)],
                   key=lambda i: (URGENCY_RANK[i["urgency"]], i.get("due_date") or "9999"))
    save(led)
    if not items:
        print("QUIET"); return
    print(json.dumps([brief(i) for i in items], indent=2))

# ------------------------------------------------------------------ work-the-list helpers
WHAT = {"declined": "payment failed", "upcoming_charge": "charge coming", "renewal": "auto-renews",
        "trial_ending": "trial converts", "price_increase": "price hike", "bill_due": "bill due", "past_due": "past due",
        "refund_owed": "refund owed", "duplicate_charge": "charged twice", "fraud_alert": "suspicious charge",
        "receipt_recurring": "recurring charge"}
NEXT = {"declined": "Update the card in the merchant's billing page", "past_due": "Pay or dispute before more fees",
        "bill_due": "Pay before the due date", "trial_ending": "Cancel before the trial converts, or keep it",
        "renewal": "Cancel before it renews, or keep it", "upcoming_charge": "Cancel or confirm before the charge",
        "price_increase": "Cancel, downgrade, or ask to keep the old price", "refund_owed": "Check the refund arrived",
        "duplicate_charge": "Ask the merchant to refund the duplicate", "fraud_alert": "Call the bank using the number on your card",
        "receipt_recurring": "Decide whether you still use it"}

def label(i):
    """<= 60 chars: merchant · amount · what's wrong (+ date). Used as a widget option label."""
    cad = UNIT.get((i.get("cadence") or "").lower(), "")
    amt = f"{m(i['amount'])}{('/' + cad) if cad else ''}" if i.get("amount") else "no amount"
    d = i.get("due_date") or i.get("charge_date") or ""
    when = " " + dt.date.fromisoformat(d[:10]).strftime("%b %-d") if d else ""
    return f"{i['merchant'][:22]} · {amt} · {WHAT[i['type']]}{when}"[:60]

def open_ranked(led, today):
    items = [i for i in led["items"] if actionable(i, today)]
    return sorted(items, key=lambda i: (URGENCY_RANK[urgency({**i, "urgency": None}, today)], -bounty(i), i.get("due_date") or "9999"))

def cmd_pick(a):
    led = load(); today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    items = open_ranked(led, today)
    page = items[a.offset:a.offset + a.limit]
    more = len(items) - a.offset - len(page)
    opts = [{"id": i["id"], "label": label(i)} for i in page]
    if more > 0:
        opts.append({"id": "__more__", "label": f"Show {min(more, a.limit)} more ({more} left)"})
    print(json.dumps({"total": len(items), "offset": a.offset, "options": opts}, indent=2))

def ics_escape(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def cmd_export(a):
    led = load(); by = {i["id"]: i for i in led["items"]}
    rows = [by[x] for x in a.ids if x in by]
    if not rows: sys.exit("no matching ledger ids")
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    def due(i):  # the day to act: the day before a renewal/trial/charge, the due date for bills, otherwise today
        d = i.get("due_date")
        if not d: return today
        early = 1 if i["type"] in ("trial_ending", "renewal", "upcoming_charge", "price_increase") else 0
        return max(today, dt.date.fromisoformat(d[:10]) - dt.timedelta(days=early))
    def title(i):
        return f"{i['merchant']}: {NEXT[i['type']].lower()}"
    def note(i):
        return f"{label(i)}. Est. {brief(i)['estimate']} ({i['savings']['basis'] or 'no $ claimed'}). From Money Watchdog."
    if a.format == "csv":  # Todoist import format; also opens fine in Sheets/Excel for Google Tasks / TickTick / Notion
        import csv, io
        buf = io.StringIO(); w = csv.writer(buf)
        w.writerow(["TYPE", "CONTENT", "DESCRIPTION", "PRIORITY", "INDENT", "AUTHOR", "RESPONSIBLE", "DATE", "DATE_LANG", "TIMEZONE"])
        for i in rows:
            pr = 1 if urgency({**i, "urgency": None}, today) == "act_now" else 2
            w.writerow(["task", title(i), note(i), pr, 1, "", "", due(i).isoformat(), "en", ""])
        txt = buf.getvalue()
    elif a.format == "ics":  # all-day calendar reminders with an alarm (Apple/Google/Outlook calendars)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ev = []
        for i in rows:
            d = due(i)
            ev += ["BEGIN:VEVENT", f"UID:{i['id']}-{d.isoformat()}@money-watchdog", f"DTSTAMP:{stamp}",
                   f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}", f"DTEND;VALUE=DATE:{(d + dt.timedelta(days=1)).strftime('%Y%m%d')}",
                   f"SUMMARY:{ics_escape(title(i))}", f"DESCRIPTION:{ics_escape(note(i))}",
                   "BEGIN:VALARM", "ACTION:DISPLAY", "TRIGGER:-PT15H", f"DESCRIPTION:{ics_escape(title(i))}", "END:VALARM",
                   "END:VEVENT"]
        txt = "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Money Watchdog//EN", *ev, "END:VCALENDAR"]) + "\r\n"
    else:
        txt = "# Money Watchdog to-do\n\n" + "".join(f"- [ ] **{title(i)}** (by {due(i).strftime('%b %-d')}): {note(i)}\n" for i in rows)
    Path(a.out).write_text(txt); print(a.out)

def cmd_show(a):
    led = load()
    rows = led["items"] if a.all else [i for i in led["items"] if i["status"] == "open"]
    for i in rows:
        b = brief(i)
        print(f"{i['id']}  {i['status']:<9} {i['type']:<17} {i['merchant'][:22]:<22} {str(i.get('amount') or ''):>8}  "
              f"due {i.get('due_date') or '-':<10}  {b['estimate']:<14} {i.get('action') or ''}")

def in_month(i, month):
    return any((i.get(k) or "").startswith(month) for k in ("first_seen", "email_date", "due_date", "charge_date"))

def crime_text(i):
    t, amt, cad = i["type"], i.get("amount"), UNIT.get((i.get("cadence") or "").lower(), "")
    per = f"/{cad}" if cad else ""
    d = i.get("due_date") or i.get("charge_date") or ""
    dd = dt.date.fromisoformat(d[:10]).strftime("%b %-d") if d else ""
    return {
        "price_increase": f"Raised the price from {m(i.get('old_amount') or 0)} to {m(amt or 0)}{per}",
        "trial_ending": f"Free trial ends {dd}, then {m(amt or 0)}{per}".replace("ends , ", "ends soon, "),
        "duplicate_charge": f"Charged {m(amt or 0)} twice{(' on ' + dd) if dd else ''}",
        "renewal": f"Auto-renews {dd} at {m(amt or 0)}{per}".replace("renews  at", "renews at"),
        "upcoming_charge": f"Plans to charge {m(amt or 0)}{(' on ' + dd) if dd else ''}",
        "bill_due": f"Bill of {m(amt or 0)} due {dd}" + (f", {m(i['late_fee'])} late fee if missed" if i.get("late_fee") else ""),
        "past_due": f"Says you're past due on {m(amt or 0)}" + (f", {m(i['late_fee'])} fee" if i.get("late_fee") else ""),
        "refund_owed": f"Owes you a {m(amt or 0)} refund",
        "fraud_alert": f"Flagged a suspicious {m(amt or 0)} charge",
        "declined": f"Payment of {m(amt or 0)} failed{(' on ' + dd) if dd else ''}",
        "receipt_recurring": f"Quietly billed {m(amt or 0)} again{(' on ' + dd) if dd else ''}",
    }[t]

def bounty(i):
    s = i["savings"]
    return (s["per_year"] if s["kind"] == "cancel_recurring" else 0) + s["one_time"]

def cmd_wanted(a):
    led = load()
    pool = [i for i in led["items"] if i["status"] == "open" and in_month(i, a.month)]
    by_m = {}
    for i in pool: by_m.setdefault(norm_merchant(i["merchant"]), []).append(i)
    if not by_m: sys.exit("no open outlaws this month; nothing to put on a poster")
    worst = max(by_m.values(), key=lambda g: sum(bounty(i) for i in g))
    worst.sort(key=lambda i: -bounty(i))
    total = sum(bounty(i) for i in worst)
    if total <= 0: sys.exit("worst offender has no dollar amount in its emails; no poster (never invent a bounty)")
    lead = worst[0]
    spec = {"type": "wanted", "merchant": lead["merchant"], "category": lead.get("category", "generic"),
            "alias": ALIAS.get(lead["type"], "The Outlaw"), "crimes": [crime_text(i) for i in worst][:3],
            "reward_per_year": round(sum(i["savings"]["per_year"] for i in worst if i["savings"]["kind"] == "cancel_recurring"), 2),
            "reward_once": round(sum(i["savings"]["one_time"] for i in worst), 2),
            "reward_basis": " + ".join(i["savings"]["basis"] for i in worst if bounty(i))[:120],
            "period": dt.date.fromisoformat(a.month + "-01").strftime("%b %Y"), "anonymous": a.anonymous,
            "slug": f"wanted-{a.month}"}
    emit(spec, a.out)

def rows_for(items):
    st = {"open": "at_large", "handled": "caught", "dismissed": "pardoned", "snoozed": "watching", "tasked": "watching"}
    rows = []
    for i in sorted(items, key=lambda i: -bounty(i)):
        s = i["savings"]
        r = {"merchant": i["merchant"], "category": i.get("category", "generic"), "crime": crime_text(i),
             "status": st.get(i["status"], "at_large")}
        if s["kind"] == "cancel_recurring": r["bounty_per_year"] = round(s["per_year"], 2)
        elif s["one_time"]: r["bounty_once"] = round(s["one_time"], 2)
        else: r["bounty_per_year"] = 0
        if i["status"] == "handled" and i.get("action") == "kept": r["status"] = "pardoned"
        rows.append(r)
    return rows

def cmd_rapsheet(a):
    led = load()
    items = [i for i in led["items"] if in_month(i, a.month)]
    spec = {"type": "rapsheet", "period": dt.date.fromisoformat(a.month + "-01").strftime("%B %Y"),
            "spotted": len(items), "rows": rows_for(items), "anonymous": a.anonymous, "slug": f"rapsheet-{a.month}"}
    emit(spec, a.out)

def cmd_board(a):
    led = load(); start = dt.date.fromisoformat(a.week_of); end = start + dt.timedelta(days=7)
    items = [i for i in led["items"] if i["status"] in ("open", "snoozed", "tasked") and
             (start.isoformat() <= i["first_seen"] < end.isoformat() or i["status"] == "open")]
    spec = {"type": "bountyboard", "period": start.strftime("%b %-d, %Y"), "rows": rows_for(items),
            "anonymous": a.anonymous, "slug": f"bountyboard-{a.week_of}"}
    emit(spec, a.out)

def emit(spec, out):
    txt = json.dumps(spec, indent=2)
    if out: Path(out).write_text(txt); print(out)
    else: print(txt)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("add"); p.add_argument("findings"); p.add_argument("--today"); p.set_defaults(fn=cmd_add)
    p = sp.add_parser("set"); p.add_argument("id"); p.add_argument("--status", required=True,
        choices=["open", "handled", "dismissed", "snoozed", "tasked"]); p.add_argument("--action",
        choices=["cancelled", "disputed", "paid", "refunded", "downgraded", "kept", "todo", "fixing", None]); p.add_argument("--note")
    p.add_argument("--snooze-until"); p.add_argument("--unused", action="store_true"); p.set_defaults(fn=cmd_set)
    p = sp.add_parser("digest"); p.add_argument("--today"); p.set_defaults(fn=cmd_digest)
    p = sp.add_parser("show"); p.add_argument("--all", action="store_true"); p.set_defaults(fn=cmd_show)
    for name, fn in (("wanted", cmd_wanted), ("rapsheet", cmd_rapsheet)):
        p = sp.add_parser(name); p.add_argument("--month", required=True); p.add_argument("--anonymous", action="store_true")
        p.add_argument("--out"); p.set_defaults(fn=fn)
    p = sp.add_parser("pick"); p.add_argument("--limit", type=int, default=5); p.add_argument("--offset", type=int, default=0)
    p.add_argument("--today"); p.set_defaults(fn=cmd_pick)
    p = sp.add_parser("export"); p.add_argument("ids", nargs="+"); p.add_argument("--format", choices=["csv", "ics", "md"], default="md")
    p.add_argument("--out", required=True); p.add_argument("--today"); p.set_defaults(fn=cmd_export)
    p = sp.add_parser("board"); p.add_argument("--week-of", required=True); p.add_argument("--anonymous", action="store_true")
    p.add_argument("--out"); p.set_defaults(fn=cmd_board)
    a = ap.parse_args(); a.fn(a)

if __name__ == "__main__":
    main()
