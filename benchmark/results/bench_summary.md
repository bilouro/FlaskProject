# Benchmark summary (median of 3 runs each)

## read

| Metric | Flask | FastAPI |
|---|---:|---:|
| Throughput (req/s) | 1,476.18 | 1,692.20 |
| Client p50 (ms) | 276.09 | 164.96 |
| Client p90 (ms) | 737.81 | 679.41 |
| Client p95 (ms) | 789.23 | 938.17 |
| Server p50 (ms) | 3.41 | 129.47 |
| Server p90 (ms) | 7.35 | 665.11 |
| Server p95 (ms) | 58.06 | 924.48 |
| Error rate | 0.00 | 0.00 |

## mixed

| Metric | Flask | FastAPI |
|---|---:|---:|
| Throughput (req/s) | 1,325.83 | 1,412.95 |
| Client p50 (ms) | 232.49 | 171.23 |
| Client p90 (ms) | 404.54 | 458.79 |
| Client p95 (ms) | 422.45 | 593.32 |
| Server p50 (ms) | 4.64 | 138.14 |
| Server p90 (ms) | 53.55 | 423.22 |
| Server p95 (ms) | 62.15 | 584.37 |
| Error rate | 0.00 | 0.00 |

## fanout

| Metric | Flask | FastAPI |
|---|---:|---:|
| Throughput (req/s) | 265.09 | 991.59 |
| Client p50 (ms) | 904.90 | 226.07 |
| Client p90 (ms) | 2,116.51 | 594.33 |
| Client p95 (ms) | 2,615.07 | 732.51 |
| Server p50 (ms) | 54.28 | 225.54 |
| Server p90 (ms) | 58.97 | 593.88 |
| Server p95 (ms) | 61.16 | 731.94 |
| Error rate | 0.00 | 0.00 |

