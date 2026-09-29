#!/usr/bin/env bash
# End-to-end tests: ledger math + dedupe, privacy gate, all poster types at both sizes.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; PY="${PY:-$ROOT/.venv/bin/python}"; T=$(mktemp -d)
export WATCHDOG_LEDGER=$T/ledger.json
echo "1) ledger add + dedupe"
out=$($PY "$ROOT/engine/ledger.py" add "$ROOT/engine/demo-findings.json" --today 2026-09-28)
echo "$out" | $PY -c "import json,sys;d=json.load(sys.stdin);assert d['new']==6 and d['repeat_sightings']==1,d;print('   ok: 7 findings -> 6 items, 1 repeat merged')"
echo "2) savings math"
$PY - <<PY
import json;L=json.load(open("$T/ledger.json"))["items"];g={(i["merchant"],i["type"]):i["savings"] for i in L}
assert abs(g[("Streamopolis+","price_increase")]["per_year"]-215.88)<.01
assert abs(g[("Streamopolis+","price_increase")]["hike_per_year"]-30.0)<.01
assert abs(g[("IronHorse Fitness","trial_ending")]["per_year"]-479.88)<.01
assert g[("Prairie Power Co.","bill_due")]["one_time"]==25
assert g[("TuneStable","receipt_recurring")]["kind"]=="review_recurring"
print("   ok: price hike, trial, late fee, review-only receipt")
PY
echo "3) digest is QUIET when nothing actionable"
WATCHDOG_LEDGER=$T/empty.json $PY "$ROOT/engine/ledger.py" digest | grep -qx QUIET && echo "   ok" || { echo "   FAIL"; exit 1; }
echo "3b) 'keep it' silences next month's identical reminder, but a new amount still alerts"
K=$T/kept.json
cat > $T/m1.json <<J
[{"thread_id":"k1","type":"renewal","merchant":"Gazette Digital","category":"news","amount":24,"cadence":"monthly","recurring":true,"email_date":"2026-09-01","due_date":"2026-09-08"}]
J
cat > $T/m2.json <<J
[{"thread_id":"k2","type":"renewal","merchant":"Gazette Digital","category":"news","amount":24,"cadence":"monthly","recurring":true,"email_date":"2026-10-01","due_date":"2026-10-08"},
 {"thread_id":"k3","type":"renewal","merchant":"Gazette Digital","category":"news","amount":29,"cadence":"monthly","recurring":true,"email_date":"2026-10-01","due_date":"2026-10-09"}]
J
WATCHDOG_LEDGER=$K $PY "$ROOT/engine/ledger.py" add $T/m1.json --today 2026-09-02 >/dev/null
id=$(WATCHDOG_LEDGER=$K $PY -c "import json;print(json.load(open('$K'))['items'][0]['id'])")
WATCHDOG_LEDGER=$K $PY "$ROOT/engine/ledger.py" set $id --status handled --action kept >/dev/null
WATCHDOG_LEDGER=$K $PY "$ROOT/engine/ledger.py" add $T/m2.json --today 2026-10-02 | $PY -c "
import json,sys;d=json.load(sys.stdin);a=d['new_actionable'];assert len(a)==1 and a[0]['amount']==29,a;print('   ok: kept \$24 stays quiet, \$29 change alerts')"
echo "3c) work-the-list: widget options (max 6, batched) + to-do export"
$PY "$ROOT/engine/ledger.py" pick --today 2026-09-28 --limit 2 | $PY -c "
import json,sys;d=json.load(sys.stdin);o=d['options'];assert d['total']==5 and len(o)==3 and o[-1]['id']=='__more__',d
assert all(len(x['label'])<=60 for x in o);print('   ok: 2 worst + show-more, labels <= 60 chars')"
$PY "$ROOT/engine/ledger.py" pick --today 2026-09-28 | $PY -c "import json,sys;assert len(json.load(sys.stdin)['options'])<=6"
ids=$($PY "$ROOT/engine/ledger.py" pick --today 2026-09-28 | $PY -c "import json,sys;print(' '.join(o['id'] for o in json.load(sys.stdin)['options'] if o['id']!='__more__'))")
for f in csv ics md; do $PY "$ROOT/engine/ledger.py" export $ids --format $f --out $T/todo.$f --today 2026-09-28 >/dev/null; done
$PY - <<PY
import csv
rows=list(csv.DictReader(open("$T/todo.csv")));assert len(rows)==5 and all(r["DATE"]>="2026-09-28" for r in rows),rows
ics=open("$T/todo.ics",newline="").read();assert ics.count("BEGIN:VEVENT")==5 and "\r\n" in ics
assert open("$T/todo.md").read().count("- [ ] ")==5
print("   ok: Todoist CSV, calendar .ics, markdown checklist (no past due dates)")
PY
first=${ids%% *}; $PY "$ROOT/engine/ledger.py" set $first --status tasked --action todo >/dev/null
$PY "$ROOT/engine/ledger.py" pick --today 2026-09-28 | $PY -c "import json,sys;d=json.load(sys.stdin);assert d['total']==4,d;print('   ok: tasked items leave the list')"
echo "3d) snooze comes back on its date; every action value the skills use is accepted"
L="$ROOT/engine/ledger.py"; rest=${ids#* }; second=${rest%% *}; third=$(echo $ids | cut -d' ' -f3)
$PY "$L" set $second --status snoozed --snooze-until 2026-10-01 >/dev/null
$PY "$L" pick --today 2026-09-28 | $PY -c "import json,sys;d=json.load(sys.stdin);assert '$second' not in [o['id'] for o in d['options']] and d['total']==3,d"
$PY "$L" set $second --status snoozed --snooze-until "next friday" >/dev/null 2>&1 && { echo "FAIL: bad snooze date accepted"; exit 1; }
$PY "$L" pick --today 2026-10-01 --limit 5 --offset 0 | $PY -c "import json,sys;d=json.load(sys.stdin);assert '$second' in [o['id'] for o in d['options']],d"
$PY "$L" digest --today 2026-10-01 >/dev/null
$PY -c "import json;i=[x for x in json.load(open('$WATCHDOG_LEDGER'))['items'] if x['id']=='$second'][0];assert i['status']=='open' and 'snooze_until' not in i,i"
$PY "$L" set $third --status open --action fixing >/dev/null || { echo "FAIL: --action fixing"; exit 1; }
for act in cancelled disputed paid refunded downgraded kept; do $PY "$L" set $third --status handled --action $act >/dev/null || { echo "FAIL: --action $act"; exit 1; }; done
echo "   ok: snoozed item wakes on Oct 1 and pings again; todo/fixing/cancelled/disputed/paid/refunded/downgraded/kept accepted"
echo "4) privacy gate blocks leaks"
cat > $T/leak.json <<J
{"type":"wanted","merchant":"LeakCo","category":"generic","crimes":["Card ending in 4821 charged \$9.99, email jo@x.com"],"reward_per_year":120,"deny_names":["Jo Smith"],"alias":"Jo Smith's nemesis"}
J
set +e; $PY "$ROOT/poster/render.py" $T/leak.json --out $T/o >/dev/null 2>$T/err; rc=$?; set -e
# scrub removes the card fragment/email and rounds; the deny-listed name in alias is scrubbed too -> render succeeds clean
if [ $rc -eq 0 ]; then ! grep -Eq "4821|jo@x|Jo Smith|9\.99" $T/o/*caption.txt && echo "   ok: scrubbed before render" || { echo "   FAIL"; exit 1; }; else echo "   ok: aborted ($rc)"; fi
echo "4b) one-time money is never shown as /yr"
cat > $T/mix.json <<J
{"type":"wanted","slug":"mix","merchant":"CloudCorral Pro","category":"cloud","crimes":["Charged \$9.99 twice on Sep 12"],"reward_per_year":24,"reward_once":9.99,"reward_basis":"hike dodged"}
J
cat > $T/once.json <<J
{"type":"wanted","slug":"once","merchant":"Boxcar Meals","category":"food","crimes":["Owes you a \$60 refund"],"reward_once":59.94,"reward_basis":"refund owed"}
J
$PY "$ROOT/poster/render.py" $T/mix.json --out $T/m --sample >/dev/null && $PY "$ROOT/poster/render.py" $T/once.json --out $T/m --sample >/dev/null
grep -q '\$24/yr + \$10 one-time' $T/m/mix-caption.txt && grep -q '\$60 one-time' $T/m/once-caption.txt && ! grep -q '/yr' $T/m/once-caption.txt && echo "   ok: mixed = \$24/yr + \$10 one-time; refund-only = \$60 one-time" || { echo "   FAIL"; exit 1; }
echo "5) render all types, both sizes"
for f in "$ROOT"/poster/examples/*.json; do $PY "$ROOT/poster/render.py" "$f" --out $T/r --sample >/dev/null; done
$PY - <<PY
from PIL import Image;import glob
fs=sorted(glob.glob("$T/r/*.png"));assert len(fs)==6,fs
for f in fs:
    w,h=Image.open(f).size;assert (w,h) in [(1200,675),(1080,1350)],(f,w,h)
print("   ok:",len(fs),"PNGs at X sizes")
PY
echo "ALL TESTS PASSED"
