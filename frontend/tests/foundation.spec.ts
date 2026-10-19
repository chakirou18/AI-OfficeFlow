import { test, expect } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  if (!process.env.DEMO_HANDLE || !process.env.DEMO_PASSWORD) throw new Error('Set private DEMO_HANDLE and DEMO_PASSWORD for browser tests')
  await page.goto('/')
  await page.getByLabel('Handle', { exact: true }).fill(process.env.DEMO_HANDLE)
  await page.getByLabel('Password', { exact: true }).fill(process.env.DEMO_PASSWORD)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible()
})

test('logout revokes access and returns to sign in', async ({ page }) => {
  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page.getByRole('heading', { name: 'Sign in to AI OfficeFlow' })).toBeVisible()
  expect((await page.request.get('/api/v1/auth/me')).status()).toBe(401)
})

test('browser talks to API, writes PostgreSQL and retrieves the same row after reload', async ({ page }) => {
  const failures: string[] = []
  page.on('pageerror', error => failures.push(error.message))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'A connected foundation.' })).toBeVisible()
  await expect(page.getByRole('region', { name: 'Service health' }).getByText('connected')).toHaveCount(3)
  await page.getByRole('button', { name: 'Save synthetic check' }).click()
  await expect(page.getByText('Synthetic check saved and retrieved')).toBeVisible()
  const id = await page.getByTestId('record-id').innerText()
  expect(id).toMatch(/^[0-9a-f-]{36}$/)
  await page.reload()
  await expect(page.getByTestId('record-id')).toHaveText(id)
  await page.screenshot({ path: '../artifacts/t04-foundation.png', fullPage: true })
  expect(failures).toEqual([])
})

test('failed database write shows an error instead of a false success', async ({ page }) => {
  await page.goto('/')
  const button = page.getByRole('button', { name: 'Save synthetic check' })
  await expect(button).toBeEnabled()
  await page.route('**/api/v1/foundation/checks', route => route.fulfill({ status: 503, json: { detail: 'Database unavailable' } }))
  await button.click()
  await expect(page.getByRole('alert')).toHaveText('The service returned HTTP 503.')
  await expect(page.getByText('Synthetic check saved and retrieved')).toHaveCount(0)
})
