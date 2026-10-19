import { useEffect, useState } from 'react'

type Health = 'checking' | 'connected' | 'unavailable'
type FoundationCheck = { id: string; marker: string; created_at: string }

async function readJson<T>(url: string, method = 'GET'): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: { Accept: 'application/json' },
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
      <footer><p>Foundation only. Request workflows, authentication and AI analysis come in later tasks.</p>
        <a href="/api/docs" target="_blank" rel="noreferrer">API documentation ↗</a>
      </footer>
    </main>
  </>
}
