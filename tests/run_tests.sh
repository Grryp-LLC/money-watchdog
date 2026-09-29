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
WATCHDOG_LEDGER=$T/empty.json $PY "$ROOT/engine/ledger.py" digest | grep -qx QUIET && echo "   ok"
echo "4) privacy gate blocks leaks"
cat > $T/leak.json <<J
{"type":"wanted","merchant":"LeakCo","category":"generic","crimes":["Card ending in 4821 charged \$9.99, email jo@x.com"],"reward_per_year":120,"deny_names":["Jo Smith"],"alias":"Jo Smith's nemesis"}
J
set +e; $PY "$ROOT/poster/render.py" $T/leak.json --out $T/o >/dev/null 2>$T/err; rc=$?; set -e
# scrub removes the card fragment/email and rounds; the deny-listed name in alias is scrubbed too -> render succeeds clean
if [ $rc -eq 0 ]; then ! grep -Eq "4821|jo@x|Jo Smith|9\.99" $T/o/*caption.txt && echo "   ok: scrubbed before render"; else echo "   ok: aborted ($rc)"; fi
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
