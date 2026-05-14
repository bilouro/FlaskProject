// I/O fanout workload — every request triggers `pg_sleep(50ms)` server-side.
//
// This is the workload async is supposed to be built for: every request
// holds a real DB connection while waiting on a slow upstream. The gap
// between sync threads and async coroutines opens here.

import http from 'k6/http';
import { check } from 'k6';
import { Trend } from 'k6/metrics';

const serverTime = new Trend('server_time_ms');

export const options = {
  stages: [
    { duration: '15s', target: 50 },
    { duration: '20s', target: 200 },
    { duration: '25s', target: 500 },
    { duration: '20s', target: 500 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],
  },
};

const BASE = __ENV.BASE || 'http://localhost:8000';
const SLEEP_MS = parseInt(__ENV.SLEEP_MS || '50', 10);

export default function () {
  const res = http.get(`${BASE}/v1/sleep?ms=${SLEEP_MS}`);
  check(res, { 'status was 200': (r) => r.status === 200 });
  const st = res.headers['X-Response-Time'];
  if (st) serverTime.add(parseFloat(st));
}
