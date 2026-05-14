# Flask vs FastAPI — side-by-side benchmark results

**Date:** 2026-05-14
**Hardware:** Apple Silicon MacBook (host), Docker Desktop. Each container
capped at **2 CPUs / 1 GB RAM** via `deploy.resources.limits`.
**Stack:**
- Postgres 16-alpine, shared by both APIs, 10,000 seeded books.
- Flask under gunicorn `-w 4 --threads 4`.
- FastAPI under uvicorn `--workers 4`.
- k6 v2.0 as load generator, running on the host (talking to containers via `localhost`).
- Three workloads, three runs each → median reported.

## Workloads

| Script | Endpoint | Ramp |
|---|---|---|
| `read` | `GET /v1/books/{random_id}` (1..10_000) | 50 → 200 → 500 → 1000 → 1000 VUs |
| `mixed` | 70% GET / 25% POST / 5% PATCH | 100 → 300 → 500 → 500 VUs |
| `fanout` | `GET /v1/sleep?ms=50` (issues `pg_sleep(50ms)` server-side) | 50 → 200 → 500 → 500 VUs |

## Results (median of 3 runs)

### `read` — read-light, no I/O wait

| Metric | Flask | FastAPI |
|---|---:|---:|
| Throughput (req/s) | **1,476** | **1,692** |
| Client p50 (ms) | 276 | 165 |
| Client p90 (ms) | 738 | 679 |
| Client p95 (ms) | 789 | 938 |
| Server p50 (ms) | 3.4 | 129 |
| Server p95 (ms) | 58 | 924 |
| Error rate | 0% | 0% |

**Reading:** FastAPI **14% higher throughput**, **40% lower client p50**.
Client p95 ties / leans Flask (the gunicorn thread pool isn't fully
saturated yet). Server-time figures diverge — see caveat below.

### `mixed` — realistic CRUD mix

| Metric | Flask | FastAPI |
|---|---:|---:|
| Throughput (req/s) | **1,326** | **1,413** |
| Client p50 (ms) | 232 | 171 |
| Client p90 (ms) | 405 | 459 |
| Client p95 (ms) | 422 | 593 |
| Server p50 (ms) | 4.6 | 138 |
| Server p95 (ms) | 62 | 584 |
| Error rate | 0% | 0% |

**Reading:** Throughput close (FastAPI +7%). Client p50 lower on FastAPI
but the tail (p95) is wider — async workers under saturation see a
heavier event-loop queue, which shows up in the p95.

### `fanout` — every request does `pg_sleep(50ms)` server-side

| Metric | Flask | FastAPI |
|---|---:|---:|
| Throughput (req/s) | **265** | **992** |
| Client p50 (ms) | 905 | 226 |
| Client p90 (ms) | 2,117 | 594 |
| Client p95 (ms) | 2,615 | 733 |
| Server p50 (ms) | 54 | 226 |
| Server p95 (ms) | 61 | 732 |
| Error rate | 0% | 0% |

**Reading:** This is the workload async is supposed to win — and it
does, clearly. **FastAPI serves ~3.7× the throughput at ~¼ the client
p50.** Flask gunicorn 4w/4t has 16 concurrent slots; once VUs > 16,
requests queue on threads, multiplying the 50 ms server-side wait by the
queue depth. FastAPI's event loop holds hundreds of in-flight
coroutines per worker without blocking, so latency stays close to the
floor (50 ms).

## Caveat — the server-time asymmetry

The `X-Response-Time` header is emitted by middleware in both apps, but
the two middlewares observe different scopes:

- **Flask**: `before_request` runs **after** gunicorn has dequeued the
  request and handed it to the worker thread. Gunicorn's own queue
  (which forms under load) is invisible to the timing.
- **FastAPI**: `@app.middleware("http")` wraps the entire ASGI lifecycle
  **inside** the uvicorn worker, including time spent waiting for the
  event loop to schedule the coroutine. Under saturation that wait is
  real and counts.

So the **server-time** numbers above measure different things, and the
comparison should not be read as "FastAPI is slower in the handler".
The **client-side** numbers (k6's `http_req_duration`) are the
apples-to-apples comparison — both APIs observed externally, same
network path, same TCP, same byte count. Those are the ones to trust
for framework comparison.

## Honest reading — what to take away

1. **Low-concurrency CRUD?** Either framework is fine. The `read` and
   `mixed` workloads show modest gaps; pick on ergonomics and team
   familiarity.
2. **I/O fanout (slow upstream calls, DB joins with sleeps, external
   APIs, fanout patterns)?** Async wins **clearly and measurably** —
   3.7× the throughput on this synthetic test. The bigger the I/O wait,
   the wider the gap. WebSockets and streaming live in this regime too.
3. **CPU-bound work?** Neither helps; both will saturate. Move to a
   worker queue or change the language.
4. **The cost of async is real** — harder debugging, smaller hiring
   pool, lazy-load-detached gotchas, libraries that aren't async-native.
   Pay that cost when the workload justifies it.

## Reproduction

```bash
docker compose -f benchmark/docker-compose-bench.yml up --build -d
# wait for both /health to return 200
python benchmark/seed.py --count 10000 --reset
bash benchmark/run.sh                  # ~26 min
python benchmark/results/aggregate.py  # writes bench_summary.csv + .md
```

All raw run JSONs are in `benchmark/results/*.json` (per-framework, per-workload, per-run).
