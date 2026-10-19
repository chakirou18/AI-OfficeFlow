let csrf = ''
export const setCsrf = (value: string) => { csrf = value }
export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}
export async function api<T>(path: string, method = 'GET', body?: unknown, idempotencyKey?: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      method, credentials: 'same-origin', signal: AbortSignal.timeout(idempotencyKey ? 40_000 : 10_000),
      headers: { Accept: 'application/json', ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(method === 'GET' ? {} : { 'X-CSRF-Token': csrf }),
        ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}) },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
  } catch { throw new Error('Unable to connect. Check your connection and retry.') }
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/api/v1/auth/')) window.dispatchEvent(new Event('session-expired'))
    throw new ApiError(response.status, response.status === 403 ? 'This action was not authorized. Refresh and try again.'
      : response.status === 422 ? 'Check the field values and try again.'
      : response.status === 404 ? 'This record could not be found.'
      : response.status === 409 ? 'This record changed or already has a conflicting decision. Refresh to review the saved result.' : `The service returned HTTP ${response.status}.`)
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>
}
