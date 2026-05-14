// Mixed workload: 70% GET, 25% POST, 5% PATCH.
//
// POSTs use a per-VU unique ISBN so duplicates don't dominate (a 409
// path is fine but distorts the throughput comparison). PATCH picks a
// random existing id and changes year only.

import http from 'k6/http';
import { check } from 'k6';
import { Trend, Counter } from 'k6/metrics';

const serverTime = new Trend('server_time_ms');
const conflicts = new Counter('isbn_conflicts');

export const options = {
  stages: [
    { duration: '15s', target: 100 },
    { duration: '20s', target: 300 },
    { duration: '25s', target: 500 },
    { duration: '20s', target: 500 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],
  },
};

const BASE = __ENV.BASE || 'http://localhost:8000';
const BOOKS = parseInt(__ENV.BOOKS || '10000', 10);
const HEADERS = { 'Content-Type': 'application/json' };

function pickAction() {
  const r = Math.random();
  if (r < 0.70) return 'get';
  if (r < 0.95) return 'post';
  return 'patch';
}

export default function () {
  const action = pickAction();
  let res;

  if (action === 'get') {
    const id = Math.floor(Math.random() * BOOKS) + 1;
    res = http.get(`${BASE}/v1/books/${id}`);
    check(res, { 'GET 200': (r) => r.status === 200 });
  } else if (action === 'post') {
    const unique = `${__VU}-${__ITER}-${Date.now()}`;
    const body = JSON.stringify({
      title: `k6 book ${unique}`,
      author: 'k6',
      year: 2026,
      isbn: `K6-${unique}`,
    });
    res = http.post(`${BASE}/v1/books`, body, { headers: HEADERS });
    if (res.status === 409) conflicts.add(1);
    check(res, { 'POST 201 or 409': (r) => r.status === 201 || r.status === 409 });
  } else {
    const id = Math.floor(Math.random() * BOOKS) + 1;
    const body = JSON.stringify({ year: 1980 + Math.floor(Math.random() * 40) });
    res = http.patch(`${BASE}/v1/books/${id}`, body, { headers: HEADERS });
    check(res, { 'PATCH 200 or 404': (r) => r.status === 200 || r.status === 404 });
  }

  const st = res.headers['X-Response-Time'];
  if (st) serverTime.add(parseFloat(st));
}
