import { test, expect } from '@playwright/test'

test('private operations routes are excluded from the frontend proxy', async ({ request }) => {
  for (const path of ['/api/v1/ops', '/api/v1/ops/health', '/api/v1/ops%2fhealth']) {
    expect((await request.get(path)).status()).toBe(404)
  }
  const api = process.env.API_URL || 'http://127.0.0.1:8000'
  expect((await request.get(`${api}/api/v1/ops/health`)).status()).toBe(403)
})
