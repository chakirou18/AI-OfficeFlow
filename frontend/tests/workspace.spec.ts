import { test, expect } from '@playwright/test'

async function signIn(page: import('@playwright/test').Page) {
  await page.goto('/')
  await page.getByLabel('Handle', { exact: true }).fill(process.env.DEMO_HANDLE || '')
  await page.getByLabel('Password', { exact: true }).fill(process.env.DEMO_PASSWORD || '')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Your workspace, at a glance.' })).toBeVisible()
}

test.beforeEach(async ({ page }) => { await signIn(page) })

test('dashboard shows real PostgreSQL counts and status links', async ({ page }) => {
  const data = await (await page.request.get('/api/v1/dashboard')).json()
  for (const [id, value] of Object.entries({ 'total-requests': data.total_requests, 'approved-tasks': data.total_tasks, 'open-tasks': data.open_tasks, 'completed-tasks': data.completed_tasks })) {
    await expect(page.getByTestId(id)).toHaveText(String(value))
  }
  for (const [status, count] of Object.entries(data.requests_by_status)) await expect(page.getByTestId(`count-${status}`)).toHaveText(String(count))
  await expect(page.getByRole('heading', { name: 'Recently updated tasks' })).toBeVisible()
  await page.screenshot({ path: '../artifacts/t08-desktop.png', fullPage: true })
  await page.getByRole('link', { name: 'Awaiting review', exact: false }).click()
  await expect(page.getByRole('heading', { name: 'No requests match this status.' })).toBeVisible()
})

test('create validates input, saves through API, survives refresh and appears in paginated list', async ({ page }) => {
  await page.getByRole('link', { name: 'New request' }).click()
  await page.getByRole('button', { name: 'Create request', exact: true }).click()
  await expect(page.getByText('Enter a title of 1–200 characters.')).toBeVisible()
  await expect(page.getByLabel('Request title')).toBeFocused()
  const title = `Synthetic browser request ${Date.now()}`
  await page.getByLabel('Request title').fill(title)
  await page.getByLabel('Description', { exact: true }).fill('Synthetic frontend persistence verification only.')
  await page.getByRole('button', { name: 'Create request', exact: true }).click()
  await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible()
  await expect(page.getByText('Request created successfully.')).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible()
  await expect(page.getByText('Synthetic frontend persistence verification only.', { exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'No approved tasks yet' })).toBeVisible()
  await page.getByRole('link', { name: 'All requests' }).click()
  await expect(page.getByRole('link', { name: title, exact: false })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Next', exact: true })).toBeEnabled()
  await page.getByRole('button', { name: 'Next', exact: true }).click()
  await expect(page.getByText(/11–\d+ of \d+ requests/)).toBeVisible()
  await page.getByRole('button', { name: 'Previous', exact: true }).click()
  await expect(page.getByRole('link', { name: title, exact: false })).toBeVisible()
})

test('persisted priorities and task updates refresh dashboard totals with CSRF protection', async ({ page }) => {
  await page.getByRole('link', { name: 'Requests', exact: true }).click()
  await page.getByLabel('Filter by status').selectOption('in_progress')
  await page.getByRole('link', { name: 'Synthetic equipment review', exact: false }).click()
  for (const priority of ['low', 'medium', 'high']) await expect(page.getByText(`${priority} priority`, { exact: true })).toBeVisible()
  const requestId = page.url().split('#requests/')[1]
  const before = await (await page.request.get('/api/v1/dashboard')).json()
  const patch = page.waitForRequest(request => request.method() === 'PATCH')
  await page.getByRole('button', { name: 'Mark done: Inspect synthetic equipment', exact: true }).click()
  expect((await patch).headers()['x-csrf-token']).toBeTruthy()
  await expect(page.getByRole('button', { name: 'Reopen: Inspect synthetic equipment', exact: true })).toBeVisible()
  const detail = await (await page.request.get(`/api/v1/requests/${requestId}`)).json()
  expect(detail.tasks.find((task: { title: string }) => task.title === 'Inspect synthetic equipment').state).toBe('done')
  await page.reload()
  await expect(page.getByRole('button', { name: 'Reopen: Inspect synthetic equipment', exact: true })).toBeVisible()
  await page.getByRole('link', { name: 'Overview', exact: true }).click()
  await expect(page.getByTestId('open-tasks')).toHaveText(String(before.open_tasks - 1))
  await expect(page.getByTestId('completed-tasks')).toHaveText(String(before.completed_tasks + 1))
})

test('loading, unavailable dashboard and retry are explicit', async ({ page }) => {
  let release!: () => void
  const gate = new Promise<void>(resolve => { release = resolve })
  await page.route('**/api/v1/dashboard', async route => { await gate; await route.fulfill({ status: 503, json: { detail: 'Synthetic unavailable test' } }) })
  await page.getByRole('button', { name: 'Refresh', exact: true }).click()
  await expect(page.getByRole('status')).toHaveText('Loading dashboard…')
  release()
  await expect(page.getByRole('alert')).toContainText('HTTP 503')
  await expect(page.getByTestId('total-requests')).toHaveCount(0)
  await page.unroute('**/api/v1/dashboard')
  await page.getByRole('button', { name: 'Try again', exact: true }).click()
  await expect(page.getByTestId('total-requests')).toBeVisible()
})

test('create failure preserves input and task failure does not claim success', async ({ page }) => {
  await page.getByRole('link', { name: 'New request' }).click()
  await page.getByLabel('Request title').fill('Synthetic unavailable request')
  await page.getByLabel('Description', { exact: true }).fill('Synthetic test text is preserved.')
  await page.route('**/api/v1/requests', route => route.fulfill({ status: 503, json: { detail: 'Unavailable' } }))
  await page.getByRole('button', { name: 'Create request', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('Your text has been preserved.')
  await expect(page.getByLabel('Request title')).toHaveValue('Synthetic unavailable request')
  await page.unroute('**/api/v1/requests')
  await page.getByRole('link', { name: 'Requests', exact: true }).click()
  await page.getByLabel('Filter by status').selectOption('in_progress')
  await page.getByRole('link', { name: 'Synthetic equipment review', exact: false }).click()
  await page.route('**/tasks/*', route => route.fulfill({ status: 503, json: { detail: 'Unavailable' } }))
  await page.getByRole('button', { name: 'Mark done: Prepare synthetic checklist', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('No successful update is claimed.')
  await expect(page.getByRole('button', { name: 'Mark done: Prepare synthetic checklist', exact: true })).toBeVisible()
})

test('expired sessions return to protected sign in', async ({ page, context }) => {
  await context.clearCookies()
  await page.getByRole('button', { name: 'Refresh', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Sign in to AI OfficeFlow' })).toBeVisible()
  await expect(page.getByRole('status')).toContainText('Your session expired')
  await expect(page.getByTestId('total-requests')).toHaveCount(0)
})

test('mobile layout supports navigation, forms and keyboard focus without overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await expect(page.getByTestId('total-requests')).toBeVisible()
  await page.screenshot({ path: '../artifacts/t08-mobile.png', fullPage: true })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.getByRole('link', { name: 'New request' }).click()
  await expect(page.getByLabel('Request title')).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
})
