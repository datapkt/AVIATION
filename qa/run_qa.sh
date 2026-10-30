#!/usr/bin/env bash
# DATAPKT full regression suite. Run from anywhere:
#   bash qa/run_qa.sh /path/to/aviation-checkout [out_dir]
# Baseline = origin/master (what is live). Candidate = the checkout's working tree.
# Pages that differ from live are passed as EXPECT_DIFF (visual change reported as NOTE, not FAIL);
# every other page must render pixel-identical. Exit code 0 only if every suite passes.
set -u
QA="$(cd "$(dirname "$0")" && pwd)"
SITE="$(cd "${1:?usage: run_qa.sh <site checkout> [out_dir]}" && pwd)"
OUT="${2:-$(mktemp -d)/dp_qa}"; mkdir -p "$OUT"
BASE="$(mktemp -d)/base"; mkdir -p "$BASE"
python3 -c 'import PIL, playwright' 2>/dev/null || pip install -q --break-system-packages pillow playwright >/dev/null
( cd "$SITE" && git fetch -q origin master 2>/dev/null; git archive origin/master | tar -x -C "$BASE" )
CHANGED=$(cd "$SITE" && { git diff --name-only origin/master -- '*.html'; git ls-files --others --exclude-standard -- '*.html'; } | sort -u | python3 -c 'import sys,json;print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')
# a change to shared CSS/JS can move any page: then nothing is pre-approved, every diff must be reviewed
SHARED=$(cd "$SITE" && git diff --name-only origin/master -- '*.css' '*.js' | head -1)
[ -n "$SHARED" ] && echo "NOTE shared CSS/JS changed ($SHARED): visual diffs on all pages are listed for review"
( cd "$BASE" && exec python3 -m http.server 8811 --bind 127.0.0.1 >/dev/null 2>&1 ) & P1=$!
( cd "$SITE" && exec python3 -m http.server 8803 --bind 127.0.0.1 >/dev/null 2>&1 ) & P2=$!
trap 'kill $P1 $P2 2>/dev/null' EXIT
for i in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:8811/ && curl -s -o /dev/null http://127.0.0.1:8803/ && break; sleep 0.5; done
export DP_SITE="$SITE" BASE_DIR="$BASE" EXPECT_DIFF="${EXPECT_DIFF:-$CHANGED}"
# set EXPECT_DIFF='[]' yourself when a change must leave every page pixel-identical (speed work)
rc=0
echo "== guard (content and structure) =="; python3 "$QA/guard.py" || rc=1
echo "== SEO / AEO / GEO / LLMO checks =="; python3 "$QA/search_checks.py" || rc=1
echo "== visual + page checks (all pages, 1440 and 390 px, home hero) =="; python3 "$QA/run_tests.py" "$OUT" || rc=1
echo "== image space, sizes, landmarks and labels =="; python3 "$QA/phase1_checks.py" || rc=1
[ -f "$QA/first_paint.py" ] && { echo "== first paint (critical CSS) =="; python3 "$QA/first_paint.py" "$OUT" || rc=1; }
echo "Screenshots: $OUT"
echo "QA RESULT: $([ $rc = 0 ] && echo PASS || echo FAIL)"
exit $rc
