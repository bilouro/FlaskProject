# Benchmark: Flask vs FastAPI, same data, same host

A repeatable side-by-side benchmark for the post 11 of the LinkedIn
series. Mirror projects share schema, ORM, validation, and error
handling — what differs is the **framework + runtime model** (sync
gunicorn vs async uvicorn). This harness isolates exactly that.

## What's measured

For three workloads — `read`, `mixed`, `fanout` — at ramped concurrency,
across both APIs running on the same host against the same Postgres,
three runs each, median reported:

- **Client side** (`http_req_duration` p50/p95/p99) — total wall-clock the
  client perceives. Includes transport + serialisation.
- **Server side** (`X-Response-Time` header p50/p95/p99) — pure framework
  time, emitted by middleware in both apps.
- **Throughput** (`http_reqs` rate).
- **Error rate** (`http_req_failed`).

The diff between **client** and **server** times tells us whether
serialisation/transport differs meaningfully between the two stacks. On
localhost it should be close to zero.

## Workloads

| Script | Endpoint | Shape | Purpose |
|---|---|---|---|
| `k6/read.js` | `GET /v1/books/{id}` (random of 10k) | ramp 50→1000 VUs | Read-light, latency-bound |
| `k6/mixed.js` | 70% GET / 25% POST / 5% PATCH | ramp 100→500 VUs | Realistic CRUD mix |
| `k6/fanout.js` | `GET /v1/sleep?ms=50` | ramp 50→500 VUs | I/O fanout — async's home turf |

## Run

```bash
# from the repo root
docker compose -f benchmark/docker-compose-bench.yml up --build -d

# wait until both report healthy
curl -sf http://localhost:5001/health && echo flask ok
curl -sf http://localhost:8000/health && echo fastapi ok

# seed 10k books (shared by both APIs via the same Postgres)
python benchmark/seed.py --count 10000

# run the full sweep (3 workloads × 2 APIs × 3 runs = 18 k6 invocations)
bash benchmark/run.sh

# aggregate to CSV + markdown table
python benchmark/results/aggregate.py
```

Final summary lands in `benchmark/results/bench_summary.md` — that table
is what gets pasted into post 11.

## Caveats to declare in the post

- **Not cloud.** Running on a developer machine. Treat as **relative**
  comparison between the two stacks under controlled identical conditions,
  not absolute production numbers.
- **Equal CPU budget.** Each container capped at 2 CPUs in compose.
- **Equal worker count.** Flask: gunicorn `-w 4 --threads 4`. FastAPI:
  uvicorn `--workers 4`. Same nominal capacity.
- **Connection pool size** uses each project's default — that itself is
  part of what each stack ships with.

## Files

```
benchmark/
├── docker-compose-bench.yml   # Postgres + flask + fastapi side by side
├── seed.py                    # ~10k books into the shared DB
├── run.sh                     # drives 18 k6 runs
├── k6/
│   ├── read.js
│   ├── mixed.js
│   └── fanout.js
└── results/
    ├── aggregate.py           # CSV + markdown table
    └── *.json                 # per-run k6 summaries (created at run time)
```
