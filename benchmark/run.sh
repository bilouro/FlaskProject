#!/usr/bin/env bash
#
# Drive the full benchmark: 3 workloads × 2 APIs × 3 runs = 18 k6 runs.
#
# Prereqs (you do these once):
#   1. docker compose -f benchmark/docker-compose-bench.yml up --build -d
#   2. wait until /health returns ok on both APIs
#   3. python benchmark/seed.py --count 10000
#   4. brew install k6  (or your equivalent)
#
# Then:  bash benchmark/run.sh
#
# Output:  benchmark/results/<framework>-<workload>-r<N>.json (k6 summary)
#
# The script is idempotent — re-running overwrites the JSON files. The
# Python aggregator (results/aggregate.py) reads all summaries and emits
# the final table for the LinkedIn post.
#
# Kept compatible with macOS's bundled bash 3.2 — no associative arrays.

set -euo pipefail

cd "$(dirname "$0")"
RESULTS=results
mkdir -p "$RESULTS"

base_url_for() {
  case "$1" in
    flask)   echo "http://localhost:5001" ;;
    fastapi) echo "http://localhost:8000" ;;
    *) echo "unknown framework: $1" >&2; exit 1 ;;
  esac
}

FRAMEWORKS="flask fastapi"
WORKLOADS="read mixed fanout"
RUNS=3

for fw in $FRAMEWORKS; do
  base=$(base_url_for "$fw")
  for w in $WORKLOADS; do
    for r in $(seq 1 $RUNS); do
      out="$RESULTS/${fw}-${w}-r${r}.json"
      echo
      echo "▶ ${fw}  ${w}  run ${r}/${RUNS}  →  ${out}"
      k6 run \
        -e BASE="$base" \
        --summary-export "$out" \
        "k6/${w}.js"
      sleep 5
    done
  done
done

echo
echo "✓ all 18 runs complete — results in $RESULTS/"
echo "  next: python $RESULTS/aggregate.py"
