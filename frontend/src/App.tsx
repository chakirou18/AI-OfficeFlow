import { useEffect, useState } from 'react'

type Health = 'checking' | 'connected' | 'unavailable'
type FoundationCheck = { id: string; marker: string; created_at: string }
type Identity = { handle: string; csrf_token: string }
let csrfToken = ''

async function readJson<T>(url: string, method = 'GET'): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: { Accept: 'application/json', ...(method !== 'GET' ? { 'X-CSRF-Token': csrfToken } : {}) },
    signal: AbortSignal.timeout(10_000),
  })
  if (!response.ok) throw new Error(`The service returned HTTP ${response.status}.`)
  return response.json() as Promise<T>
}

function ServiceCard({ name, status, detail }: { name: string; status: Health; detail: string }) {
  return <article className="service-card">
    <div className="service-top"><h2>{name}</h2><span className={`status ${status}`}>{status}</span></div>
    <p>{detail}</p>
  </article>
}

export function App() {
  const [identity, setIdentity] = useState<Identity | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  useEffect(() => {
    readJson<Identity>('/api/v1/auth/me').then(value => {
      csrfToken = value.csrf_token
      setIdentity(value)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])
  if (loading) return <main><p>Checking session…</p></main>
  if (!identity) return <main><h1>Sign in to AI OfficeFlow</h1>
    <p>Controlled demo accounts only. Use synthetic data.</p>
    <form onSubmit={async event => {
      event.preventDefault()
      const data = new FormData(event.currentTarget)
      setError('')
      try {
        const response = await fetch('/api/v1/auth/login', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ handle: data.get('handle'), password: data.get('password') }),
          signal: AbortSignal.timeout(10_000),
        })
        if (!response.ok) throw new Error('Sign-in failed. Check your credentials or retry later.')
        const value = await response.json() as Identity
        csrfToken = value.csrf_token
        setIdentity(value)
      } catch (cause) { setError(cause instanceof Error ? cause.message : 'Sign-in unavailable.') }
    }}>
      <p><label>Handle <input name="handle" autoComplete="username" maxLength={40} required /></label></p>
      <p><label>Password <input name="password" type="password" autoComplete="current-password" maxLength={128} required /></label></p>
      <button type="submit">Sign in</button>
    </form>{error && <p role="alert">{error}</p>}
  </main>
  return <><div className="topbar"><span>Signed in as {identity.handle}</span>
    <button onClick={async () => {
      try {
        const response = await fetch('/api/v1/auth/logout', { method: 'POST', headers: { 'X-CSRF-Token': csrfToken } })
        if (!response.ok && response.status !== 401) throw new Error('Sign-out failed. Please retry.')
        csrfToken = ''
        setIdentity(null)
      } catch { setError('Sign-out unavailable. Please retry.') }
    }}>Sign out</button>{error && <p role="alert">{error}</p>}
  </div><FoundationApp /></>
}

function FoundationApp() {
  const [api, setApi] = useState<Health>('checking')
  const [database, setDatabase] = useState<Health>('checking')
  const [record, setRecord] = useState<FoundationCheck | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    readJson('/api/v1/health/live').then(
      () => { if (active) setApi('connected') },
      () => { if (active) setApi('unavailable') },
    )
    readJson('/api/v1/health/ready').then(
      () => { if (active) setDatabase('connected') },
      () => { if (active) setDatabase('unavailable') },
    )
    const id = new URLSearchParams(window.location.search).get('check')
    if (id) readJson<FoundationCheck>(`/api/v1/foundation/checks/${encodeURIComponent(id)}`).then(
      value => { if (active) setRecord(value) },
      () => { if (active) setError('The saved check could not be loaded. Check service availability and the record ID.') },
    )
    return () => { active = false }
  }, [])

  async function saveCheck() {
    setBusy(true)
    setError('')
    try {
      const saved = await readJson<FoundationCheck>('/api/v1/foundation/checks', 'POST')
      const fetched = await readJson<FoundationCheck>(`/api/v1/foundation/checks/${saved.id}`)
      setRecord(fetched)
      const url = new URL(window.location.href)
      url.searchParams.set('check', fetched.id)
      window.history.replaceState(null, '', url)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The database check failed. Please retry.')
    } finally {
      setBusy(false)
    }
  }

  return <>
    <header className="topbar">
      <a className="brand" href="/"><span className="brand-icon" aria-hidden="true">of</span>AI OfficeFlow</a>
      <span className="project-label">ZOOMCAMP 2026 <span>/</span> T04</span>
    </header>
    <main>
      <div className="intro"><p className="eyebrow">LOCAL DEVELOPMENT</p>
        <h1>A connected foundation.</h1>
        <p className="lede">The first step toward simpler request management. Verify the application and its persistent database below.</p>
      </div>
      <section className="services" aria-label="Service health">
        <ServiceCard name="Frontend" status="connected" detail="React · TypeScript · Vite" />
        <ServiceCard name="API" status={api} detail="Python · FastAPI" />
        <ServiceCard name="Database" status={database} detail="PostgreSQL · Alembic migrations" />
      </section>
      <section className="verification" aria-labelledby="check-title">
        <div className="verification-copy"><p className="eyebrow">END-TO-END CHECK</p>
          <h2 id="check-title">A small write. A real round trip.</h2>
          <p>Save a fixed synthetic record through the API, then read it back from PostgreSQL. Reload this page to retrieve the same saved record.</p>
          <button onClick={saveCheck} disabled={busy || database !== 'connected'}>{busy ? 'Saving and reading…' : 'Save synthetic check'}<span aria-hidden="true"> ↗</span></button>
          {error && <p className="error" role="alert">{error}</p>}
        </div>
        <div className="record-panel" aria-live="polite">
          {record ? <><span className="record-label">SAVED TO POSTGRESQL</span>
            <p className="saved-title">Synthetic check saved and retrieved</p>
            <dl><dt>Record ID</dt><dd data-testid="record-id">{record.id}</dd>
              <dt>Created</dt><dd>{new Date(record.created_at).toLocaleString()}</dd>
              <dt>Marker</dt><dd>{record.marker}</dd></dl>
          </> : <><span className="record-label">NO CHECK SELECTED</span>
            <p className="empty-title">Your saved record will appear here.</p>
            <p>Only synthetic connectivity data is written. No customer or request data is collected.</p>
          </>}
        </div>
      </section>
      <footer><p>Authenticated foundation. Request workflows and AI analysis come in later tasks.</p>
        <a href="/api/docs" target="_blank" rel="noreferrer">API documentation ↗</a>
      </footer>
    </main>
  </>
}
