import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'
import { formatApiError } from '../src/api/errors'

const college = { id: 1, name: 'Demo College', institution_type: 'community_college' }
const campuses = [
  { id: 10, name: 'Demo Campus A', institution_type: 'university' },
  { id: 20, name: 'Demo Campus B', institution_type: 'university' },
]
const majors = [
  { id: 101, name: 'Demo Major A', institution_id: 10 },
  { id: 201, name: 'Demo Major B', institution_id: 20 },
]

test.beforeEach(async ({ page }) => {
  // Every API call is intercepted; these tests cannot write to the real database.
  await page.route('http://127.0.0.1:18080/**', async (route) => {
    const url = new URL(route.request().url())
    const data = url.pathname === '/health' ? { status: 'healthy' }
      : url.pathname === '/api/v1/institutions' ? [college]
      : url.pathname === '/api/v1/campuses' ? campuses
      : url.pathname === '/api/v1/majors' ? majors.filter((major) => major.institution_id === Number(url.searchParams.get('institution_id')))
      : null
    await route.fulfill({ status: data ? 200 : 404, json: data })
  })
})

async function fillProfile(page: Page) {
  await page.goto('/')
  await page.getByLabel('Current community college').selectOption('1')
  await page.getByLabel('Target UC/CSU campus').selectOption('10')
  await page.getByLabel('Intended major').selectOption('101')
}

test('stale campus responses cannot overwrite the latest selection', async ({ page }) => {
  let release!: () => void
  const pending = new Promise<void>((resolve) => { release = resolve })
  let requested!: () => void
  const started = new Promise<void>((resolve) => { requested = resolve })
  await page.route('**/api/v1/majors?institution_id=10', async (route) => {
    requested()
    await pending
    await route.fulfill({ json: [majors[0]] }).catch(() => {}) // Request may already be aborted.
  })
  await page.goto('/')
  await page.getByLabel('Target UC/CSU campus').selectOption('10')
  await started
  await page.getByLabel('Target UC/CSU campus').selectOption('20')
  await expect(page.getByRole('option', { name: 'Demo Major B' })).toHaveCount(1)
  release()
  await expect(page.getByLabel('Intended major')).toBeEnabled()
  await expect(page.getByRole('option', { name: 'Demo Major A' })).toHaveCount(0)
  await page.getByLabel('Intended major').selectOption('201')
})

test('pending saves cannot be submitted twice and show the saved profile', async ({ page }) => {
  let submissions = 0
  let release!: () => void
  const pending = new Promise<void>((resolve) => { release = resolve })
  await page.route('**/api/v1/student-profiles', async (route) => {
    submissions += 1
    await pending
    await route.fulfill({ status: 201, json: {
      id: 1, current_college: college, anticipated_transfer_term: 'Fall 2027',
      created_at: '2026-10-28T00:00:00Z',
      targets: [{ target_campus: campuses[0], intended_major: majors[0] }],
    } })
  })
  await fillProfile(page)
  await page.getByRole('button', { name: 'Save profile' }).click()
  await expect(page.getByRole('button', { name: 'Saving…' })).toBeDisabled()
  // Check the synchronous submission guard too, beyond the disabled button.
  await page.locator('form').dispatchEvent('submit')
  await expect.poll(() => submissions).toBe(1)
  release()
  await expect(page.getByText('Profile saved successfully.')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Saved profile' })).toBeVisible()
  expect(submissions).toBe(1)
})

test('validation errors are readable and a failed save can be retried', async ({ page }) => {
  await page.route('**/api/v1/student-profiles', (route) => route.fulfill({ status: 422, json: {
    detail: [{ loc: ['body', 'anticipated_transfer_term'], msg: 'Use a season and four-digit year' }],
  } }))
  await fillProfile(page)
  await expect(page.getByText(/Demonstration catalog:/)).toBeVisible()
  await page.getByRole('button', { name: 'Save profile' }).click()
  await expect(page.getByRole('alert')).toHaveText('anticipated_transfer_term: Use a season and four-digit year')
  await expect(page.getByRole('button', { name: 'Save profile' })).toBeEnabled()
})

test('a catalog failure is reported separately from backend health', async ({ page }) => {
  await page.route('**/api/v1/institutions', (route) => route.fulfill({ status: 500, json: { detail: 'Internal Server Error' } }))
  await page.goto('/')
  await expect(page.getByText('Backend: healthy')).toBeVisible()
  await expect(page.getByRole('alert')).toContainText('Could not load the demonstration catalog')
})

test('API error formatting handles strings, malformed bodies, and validation arrays', () => {
  expect(formatApiError({ detail: 'Not found' }, 404)).toBe('Not found')
  expect(formatApiError(null, 500)).toContain('500')
  expect(formatApiError({ detail: [{ missing: true }] }, 422)).toContain('422')
  expect(formatApiError({ detail: [{ loc: ['body', 'targets', 0], msg: 'Invalid target' }] }, 422))
    .toBe('targets.0: Invalid target')
})
