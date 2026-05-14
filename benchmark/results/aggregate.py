"""Aggregate k6 JSON summaries into a single CSV + markdown table.

Reads every `*-r<N>.json` under this directory, groups by (framework,
workload), takes the median across the 3 runs, and emits:

  - bench_summary.csv : machine-readable
  - bench_summary.md  : ready to paste into the LinkedIn post 11

Run after `bash benchmark/run.sh` completes.
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import statistics
from collections import defaultdict


DIR = os.path.dirname(os.path.abspath(__file__))
PATTERN = re.compile(r"^(flask|fastapi)-(read|mixed|fanout)-r(\d+)\.json$")


def load_summaries() -> dict[tuple[str, str], list[dict]]:
    by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for path in sorted(glob.glob(os.path.join(DIR, "*.json"))):
        m = PATTERN.match(os.path.basename(path))
        if not m:
            continue
        fw, wl, _ = m.group(1), m.group(2), m.group(3)
        with open(path) as f:
            by_key[(fw, wl)].append(json.load(f))
    return by_key


def metric(summary: dict, name: str, agg: str) -> float | None:
    """Pull a specific aggregate out of k6's `metrics` block.

    k6 v2.0 emits flat metric dicts: {avg, min, med, max, p(90), p(95), count, rate}.
    Older versions nested under "values". We probe both.
    """
    m = summary.get("metrics", {}).get(name) or {}
    if isinstance(m.get("values"), dict):
        m = m["values"]
    val = m.get(agg)
    return float(val) if val is not None else None


def median_across_runs(runs: list[dict], name: str, agg: str) -> float | None:
    vals = [v for v in (metric(r, name, agg) for r in runs) if v is not None]
    return statistics.median(vals) if vals else None


def main() -> int:
    by_key = load_summaries()
    if not by_key:
        print("no k6 summary files found — run bash run.sh first")
        return 1

    rows = []
    for (fw, wl), runs in sorted(by_key.items()):
        rows.append({
            "framework": fw,
            "workload": wl,
            "runs": len(runs),
            "rps_median": median_across_runs(runs, "http_reqs", "rate"),
            # k6 v2.0 exports `med` (= p50) and `p(90)`, `p(95)` but no p(99) by
            # default — use what's available.
            "client_p50_ms": median_across_runs(runs, "http_req_duration", "med"),
            "client_p90_ms": median_across_runs(runs, "http_req_duration", "p(90)"),
            "client_p95_ms": median_across_runs(runs, "http_req_duration", "p(95)"),
            "server_p50_ms": median_across_runs(runs, "server_time_ms", "med"),
            "server_p90_ms": median_across_runs(runs, "server_time_ms", "p(90)"),
            "server_p95_ms": median_across_runs(runs, "server_time_ms", "p(95)"),
            "errors_pct": median_across_runs(runs, "http_req_failed", "value"),
        })

    # CSV
    csv_path = os.path.join(DIR, "bench_summary.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {csv_path}")

    # Markdown — grouped by workload, side-by-side
    md_path = os.path.join(DIR, "bench_summary.md")
    with open(md_path, "w") as f:
        f.write("# Benchmark summary (median of 3 runs each)\n\n")
        for wl in ["read", "mixed", "fanout"]:
            f.write(f"## {wl}\n\n")
            f.write(
                "| Metric | Flask | FastAPI |\n"
                "|---|---:|---:|\n"
            )

            def fmt(x, suffix=""):
                if x is None:
                    return "—"
                return f"{x:,.2f}{suffix}"

            rows_for_wl = {r["framework"]: r for r in rows if r["workload"] == wl}
            flask = rows_for_wl.get("flask", {})
            fastapi = rows_for_wl.get("fastapi", {})

            for label, key, suffix in [
                ("Throughput (req/s)", "rps_median", ""),
                ("Client p50 (ms)", "client_p50_ms", ""),
                ("Client p90 (ms)", "client_p90_ms", ""),
                ("Client p95 (ms)", "client_p95_ms", ""),
                ("Server p50 (ms)", "server_p50_ms", ""),
                ("Server p90 (ms)", "server_p90_ms", ""),
                ("Server p95 (ms)", "server_p95_ms", ""),
                ("Error rate", "errors_pct", ""),
            ]:
                f.write(
                    f"| {label} | {fmt(flask.get(key), suffix)} "
                    f"| {fmt(fastapi.get(key), suffix)} |\n"
                )
            f.write("\n")

    print(f"wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
