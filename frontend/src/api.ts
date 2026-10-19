let csrf = ''
function newTrace() { return `00-${crypto.randomUUID().replaceAll('-', '')}-${crypto.randomUUID().replaceAll('-', '').slice(0, 16)}-01` }
let traceparent = newTrace()
export const setCsrf = (value: string) => { csrf = value }
export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}
export async function api<T>(path: string, method = 'GET', body?: unknown, idempotencyKey?: string): Promise<T> {
  let response: Response
  try {
    if (path === '/api/v1/auth/login') traceparent = newTrace()
    response = await fetch(path, {
      method, credentials: 'same-origin', signal: AbortSignal.timeout(idempotencyKey ? 40_000 : 10_000),
      headers: { Accept: 'application/json', traceparent, ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(method === 'GET' ? {} : { 'X-CSRF-Token': csrf }),
        ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}) },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
  } catch { throw new Error('Unable to connect. Check your connection and retry.') }
  const returnedContext = response.headers.get('traceparent')
  if (returnedContext && /^00-[0-9a-f]{32}-[0-9a-f]{16}-01$/.test(returnedContext)) traceparent = returnedContext
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/api/v1/auth/')) window.dispatchEvent(new Event('session-expired'))
    throw new ApiError(response.status, response.status === 403 ? 'This action was not authorized. Refresh and try again.'
      : response.status === 422 ? 'Check the field values and try again.'
      : response.status === 404 ? 'This record could not be found.'
      : response.status === 409 ? 'This record changed or already has a conflicting decision. Refresh to review the saved result.' : `The service returned HTTP ${response.status}.`)
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>
}
