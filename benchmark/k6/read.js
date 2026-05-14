// Read-light workload: GET a random book by id.
//
// Ramps 50 → 500 → 1000 VUs over ~90s. Reads the X-Response-Time header
// emitted by the API middleware and records it as a custom metric, so we
// can compare framework time (X-Response-Time) vs total wall-clock
// (http_req_duration).
//
// Usage:
//   k6 run -e BASE=http://localhost:8000 -e TAG=fastapi-read-r1 \
//          --summary-export=results/fastapi-read-r1.json \
//          benchmark/k6/read.js

import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';

const serverTime = new Trend('server_time_ms');

export const options = {
  stages: [
    { duration: '15s', target: 50 },
    { duration: '15s', target: 200 },
    { duration: '20s', target: 500 },
    { duration: '20s', target: 1000 },
    { duration: '20s', target: 1000 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<2000'],
  },
};

const BASE = __ENV.BASE || 'http://localhost:8000';
const BOOKS = parseInt(__ENV.BOOKS || '10000', 10);

export default function () {
  const id = Math.floor(Math.random() * BOOKS) + 1;
  const res = http.get(`${BASE}/v1/books/${id}`);

  check(res, { 'status was 200': (r) => r.status === 200 });

  const st = res.headers['X-Response-Time'];
  if (st) serverTime.add(parseFloat(st));
}
