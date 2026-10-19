import { test, expect } from '@playwright/test'

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
