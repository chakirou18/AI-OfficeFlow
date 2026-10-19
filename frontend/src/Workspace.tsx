import { useEffect, useState } from 'react'
import { api } from './api'
import { FoundationApp } from './Foundation'
import { statusLabels } from './types'
import type { AnalysisConfig, Dashboard, Detail, Page, RequestItem, Status, Task } from './types'

type Route = { view: string; id?: string }
function currentRoute(): Route {
  const [view, id] = window.location.hash.slice(1).split('/')
  return { view: (view || 'dashboard').split('?')[0], id }
}
const date = (value: string) => new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
export function Badge({ status }: { status: Status }) { return <span className={`badge ${status}`}>{statusLabels[status]}</span> }
function ErrorBox({ message, retry }: { message: string; retry: () => void }) {
  return <div className="error" role="alert">{message} <button className="text-button" onClick={retry}>Try again</button></div>
}
function RequestRows({ items }: { items: RequestItem[] }) {
  return <ul className="request-rows">{items.map(item => <li key={item.id}>
    <a href={`#requests/${item.id}`} className="request-link"><span className="request-mark" aria-hidden="true">↗</span><span><strong>{item.title}</strong><small>{item.creator_handle} · {date(item.created_at)}</small></span></a>
    <Badge status={item.status} />
  </li>)}</ul>
}

export function Workspace({ handle, logout, signingOut, authError }: { handle: string; logout: () => Promise<void>; signingOut: boolean; authError: string }) {
  const [route, setRoute] = useState(currentRoute)
  const [revision, setRevision] = useState(0)
  const [summary, setSummary] = useState<Dashboard | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState('')
  useEffect(() => { const changed = () => { setRoute(currentRoute()); setNotice('') }; window.addEventListener('hashchange', changed); return () => window.removeEventListener('hashchange', changed) }, [])
  useEffect(() => {
    let active = true
    setLoading(true); setError('')
    api<Dashboard>('/api/v1/dashboard').then(value => { if (active) setSummary(value) })
      .catch(cause => { if (active) { setSummary(null); setError(cause.message) } }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [revision, route.view])
  const refresh = () => setRevision(value => value + 1)
  return <div className="app-layout"><a className="skip-link" href="#main-content" onClick={event => { event.preventDefault(); document.getElementById('main-content')?.focus() }}>Skip to content</a>
    <aside className="sidebar"><a className="brand" href="#dashboard"><span className="brand-icon">of</span>AI OfficeFlow</a>
      <p className="nav-label">WORKSPACE</p><nav aria-label="Main navigation">
        <a href="#dashboard" aria-current={route.view === 'dashboard' ? 'page' : undefined}><span aria-hidden="true">▦</span>Overview</a>
        <a href="#requests" aria-current={route.view === 'requests' || route.view === 'new' ? 'page' : undefined}><span aria-hidden="true">▤</span>Requests</a>
        <a href="#foundation" aria-current={route.view === 'foundation' ? 'page' : undefined}><span aria-hidden="true">◉</span>System health</a>
      </nav><div className="sidebar-note"><span className="live-dot" />Synthetic workspace<p>Small requests.<br />Clear next steps.</p></div>
      <div className="account"><span className="avatar" aria-hidden="true">{handle.slice(0, 2).toUpperCase()}</span><div><strong>{handle}</strong><small>Demo account</small></div>
        <button className="text-button" disabled={signingOut} onClick={() => void logout()}>Sign out</button></div>
    </aside>
    <div className="workspace"><header className="workspace-bar"><span>Workspace <span className="muted">/ {route.view === 'dashboard' ? 'Overview' : route.view === 'foundation' ? 'System health' : 'Requests'}</span></span><span className="demo-pill">SYNTHETIC DEMO</span></header>
    <main id="main-content" className="workspace-main" tabIndex={-1}>
      {authError && <p className="error" role="alert">{authError}</p>}
      {notice && <p className="success" role="status">{notice}</p>}
      {route.view === 'foundation' ? <FoundationApp /> : <>
        <div className="page-heading"><div><p className="eyebrow">A LITTLE STRUCTURE. A LOT MORE CLARITY.</p>
          <h1>{route.view === 'dashboard' ? 'Your workspace, at a glance.' : route.view === 'new' ? 'Start with a request.' : route.id ? 'Request details' : 'Every request. One place.'}</h1>
          <p className="muted">{route.view === 'dashboard' ? 'See what’s new, what’s moving, and what’s done.' : 'Capture the details and keep the next steps in view.'}</p></div>
          <div className="heading-actions"><button className="secondary" onClick={refresh} disabled={loading}>Refresh</button><a className="button primary" href="#new">＋ New request</a></div>
        </div>
        {route.view === 'dashboard' ? <>
          {loading ? <p role="status" className="loading">Loading dashboard…</p> : error ? <ErrorBox message={error} retry={refresh} /> : summary && <>
            <section className="stats" aria-label="Workspace statistics">
              {([['Total requests', summary.total_requests, 'All captured work'], ['Approved tasks', summary.total_tasks, 'Persisted task records'], ['Open tasks', summary.open_tasks, 'Ready to move forward'], ['Completed tasks', summary.completed_tasks, 'Work checked off']] as const).map(([label, value, description]) => <article className="stat-card" key={label}><p>{label}</p><strong data-testid={label.toLowerCase().replaceAll(' ', '-')}>{value}</strong><small>{description}</small></article>)}
            </section>
            <section className="status-strip" aria-label="Requests by status">{(Object.keys(statusLabels) as Status[]).map(status => <a href={`#requests?status=${status}`} key={status}><Badge status={status} /><strong data-testid={`count-${status}`}>{summary.requests_by_status[status]}</strong></a>)}</section>
            <div className="dashboard-columns"><section className="panel"><div className="panel-heading"><div><h2>Recent requests</h2><p>The latest additions to your workspace.</p></div><a className="text-link" href="#requests">View all →</a></div>
              {summary.recent_requests.length ? <RequestRows items={summary.recent_requests} /> : <div className="empty"><h3>A clear space for your next request.</h3><p>Create your first synthetic request to get started.</p><a className="button primary" href="#new">Create a request</a></div>}
            </section><section className="panel"><div className="panel-heading"><div><h2>Recently updated tasks</h2><p>Current state from your saved work.</p></div></div>
              {summary.recent_tasks.length ? <ul className="activity-list">{summary.recent_tasks.map(task => <li key={task.id}><span className={`task-dot ${task.state}`} /><div><a href={`#requests/${task.request_id}`}>{task.title}</a><small>{task.state === 'done' ? 'Done' : 'Open'} · {date(task.updated_at)}</small></div></li>)}</ul> : <div className="empty"><h3>No approved tasks yet</h3><p>Approved tasks will appear here when available.</p></div>}
            </section></div>
          </>}
        </> : route.view === 'new' ? <RequestForm onCreated={id => { refresh(); window.location.hash = `requests/${id}`; setTimeout(() => setNotice('Request created successfully.'), 0) }} />
          : route.view.startsWith('requests') ? route.id ? <RequestDetail key={route.id} id={route.id} revision={revision} changed={message => { refresh(); setNotice(message) }} /> : <RequestList key={window.location.hash} revision={revision} />
          : <div className="empty"><h2>Page not found</h2><a href="#dashboard">Return to overview</a></div>}
      </>}
      <footer className="workspace-footer"><span>AI OfficeFlow · Zoomcamp 2026</span><span>Synthetic data only</span></footer>
    </main></div>
  </div>
}

function RequestForm({ onCreated }: { onCreated: (id: string) => void }) {
  const [title, setTitle] = useState(''); const [description, setDescription] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({}); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  return <section className="panel form-panel"><h2>What needs to happen?</h2><p className="muted">Use synthetic information only. Saved request text cannot be edited.</p>
    <form noValidate onSubmit={async event => {
      event.preventDefault()
      const issues: Record<string, string> = {}
      if (!title.trim() || title.trim().length > 200) issues.title = 'Enter a title of 1–200 characters.'
      if (!description.trim() || description.trim().length > 5000) issues.description = 'Enter a description of 1–5,000 characters.'
      setErrors(issues); setError(''); if (Object.keys(issues).length) { document.getElementById(Object.keys(issues)[0])?.focus(); return }
      setBusy(true)
      try { const saved = await api<Detail>('/api/v1/requests', 'POST', { title: title.trim(), description: description.trim() }); onCreated(saved.id) }
      catch (cause) { setError(cause instanceof Error ? cause.message : 'Request could not be saved.') }
      finally { setBusy(false) }
    }}>
      <label htmlFor="title">Request title</label><input id="title" value={title} onChange={event => setTitle(event.target.value)} maxLength={200} required aria-invalid={!!errors.title} aria-describedby="title-help title-error" placeholder="e.g. Prepare the monthly stock review" />
      <div className="field-meta"><small id="title-help">A short, specific title.</small><small>{title.length}/200</small></div>{errors.title && <p className="field-error" id="title-error">{errors.title}</p>}
      <label htmlFor="description">Description</label><textarea id="description" value={description} onChange={event => setDescription(event.target.value)} maxLength={5000} rows={7} required aria-invalid={!!errors.description} aria-describedby="description-help description-error" placeholder="Describe the request and any useful context…" />
      <div className="field-meta"><small id="description-help">Include enough context for someone to understand the work.</small><small>{description.length}/5,000</small></div>{errors.description && <p className="field-error" id="description-error">{errors.description}</p>}
      {error && <p className="error" role="alert">{error} Your text has been preserved.</p>}
      <div className="form-actions"><a className="button secondary" href="#requests">Cancel</a><button className="primary" disabled={busy} type="submit">{busy ? 'Saving…' : 'Create request'}</button></div>
    </form></section>
}

function RequestList({ revision }: { revision: number }) {
  const query = new URLSearchParams(window.location.hash.split('?')[1] || '')
  const [filter, setFilter] = useState(query.get('status') || '')
  const [offset, setOffset] = useState(0); const [page, setPage] = useState<Page | null>(null)
  const [error, setError] = useState(''); const [loading, setLoading] = useState(true); const [retry, setRetry] = useState(0)
  useEffect(() => {
    let active = true; setLoading(true); setError('')
    api<Page>(`/api/v1/requests?limit=10&offset=${offset}${filter ? `&status=${encodeURIComponent(filter)}` : ''}`)
      .then(value => { if (active) setPage(value) }).catch(cause => { if (active) setError(cause.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [filter, offset, revision, retry])
  return <section className="panel"><div className="panel-heading"><div><h2>Request register</h2><p>Original details, current status, and a clear next step.</p></div>
    <div><label className="sr-only" htmlFor="filter">Filter by status</label><select id="filter" value={filter} onChange={event => { setFilter(event.target.value); setOffset(0) }}><option value="">All statuses</option>{(Object.keys(statusLabels) as Status[]).map(status => <option key={status} value={status}>{statusLabels[status]}</option>)}</select></div></div>
    {loading ? <p role="status" className="loading">Loading requests…</p> : error ? <ErrorBox message={error} retry={() => setRetry(value => value + 1)} /> : page && <>
      {page.items.length ? <RequestRows items={page.items} /> : <div className="empty"><h3>{filter ? 'No requests match this status.' : 'No requests yet.'}</h3><p>{filter ? 'Choose another status or create a new request.' : 'Your saved requests will appear here.'}</p></div>}
      <div className="pagination"><span>{page.total ? `${offset + 1}–${Math.min(offset + page.limit, page.total)}` : '0'} of {page.total} requests</span><div><button className="secondary" disabled={offset === 0} onClick={() => setOffset(value => Math.max(0, value - 10))}>Previous</button><button className="secondary" disabled={offset + 10 >= page.total || offset >= 10000} onClick={() => setOffset(value => value + 10)}>Next</button></div></div>
    </>}
  </section>
}

function RequestDetail({ id, revision, changed }: { id: string; revision: number; changed: (message: string) => void }) {
  const [reason, setReason] = useState(''); const [decisionError, setDecisionError] = useState('')
  const [config, setConfig] = useState<AnalysisConfig | null>(null)
  const [analysisError, setAnalysisError] = useState('')
  const [detail, setDetail] = useState<Detail | null>(null); const [loading, setLoading] = useState(true)
  const [error, setError] = useState(''); const [mutationError, setMutationError] = useState(''); const [busy, setBusy] = useState(''); const [retry, setRetry] = useState(0)
  useEffect(() => {
    let active = true; setLoading(true); setError('')
    api<Detail>(`/api/v1/requests/${encodeURIComponent(id)}`).then(value => { if (active) setDetail(value) })
      .catch(cause => { if (active) setError(cause.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [id, revision, retry])
  useEffect(() => {
    api<AnalysisConfig>('/api/v1/requests/analysis/config').then(setConfig).catch(() => setConfig(null))
  }, [])
  async function analyze() {
    setBusy('analysis'); setAnalysisError('')
    try { await api(`/api/v1/requests/${id}/analyses`, 'POST', undefined, crypto.randomUUID()) }
    catch (cause) { setAnalysisError(cause instanceof Error ? cause.message : 'Analysis failed.') }
    finally { setBusy(''); setRetry(value => value + 1) }
  }
  async function update(task: Task) {
    setBusy(task.id); setMutationError('')
    try { await api(`/api/v1/requests/${id}/tasks/${task.id}`, 'PATCH', { state: task.state === 'open' ? 'done' : 'open' }); changed('Task status updated.') }
    catch (cause) { setMutationError(cause instanceof Error ? cause.message : 'Task could not be updated.') }
    finally { setBusy('') }
  }
  async function decide(analysisId: string, decision: 'approve' | 'reject') {
    setDecisionError('')
    if (decision === 'reject' && !reason.trim()) {
      setDecisionError('Enter a rejection reason of 1–1,000 characters.'); document.getElementById('rejection-reason')?.focus(); return
    }
    setBusy('decision')
    try {
      await api(`/api/v1/requests/${id}/analyses/${analysisId}/decision`, 'POST', { decision, ...(decision === 'reject' ? { reason: reason.trim() } : {}) })
      setReason(''); changed(decision === 'approve' ? 'Suggestions approved. Tasks saved.' : 'Suggestions rejected. No tasks created.')
    } catch (cause) { setDecisionError(cause instanceof Error ? cause.message : 'Decision could not be saved.') }
    finally { setBusy(''); setRetry(value => value + 1) }
  }
  return <><a className="text-link back-link" href="#requests">← All requests</a>
    {loading ? <p role="status" className="loading">Loading request…</p> : error ? <ErrorBox message={error} retry={() => setRetry(value => value + 1)} /> : detail && <>
      <article className="panel request-detail"><div className="detail-title"><h2>{detail.title}</h2><Badge status={detail.status} /></div>
        <p className="muted">Created by {detail.creator_handle} · {date(detail.created_at)}</p><h3>Description</h3><p className="request-description">{detail.description}</p>
        <dl className="detail-meta"><div><dt>Request ID</dt><dd>{detail.id}</dd></div><div><dt>Last updated</dt><dd>{date(detail.updated_at)}</dd></div></dl></article>
      <section className="panel"><div className="panel-heading"><div><h2>Analysis suggestions</h2>
        <p>{config ? config.provider_mode === 'simulated' ? 'Simulated mode · deterministic offline output' : `Real local model · Ollama ${config.provider_model}` : 'Analysis configuration unavailable'}</p></div>
        {!detail.tasks.length && (!detail.analysis || ['failed', 'rejected'].includes(detail.analysis.state)) && <button className="primary" disabled={!!busy || !config} onClick={() => void analyze()}>{busy === 'analysis' ? 'Analyzing… (up to 30 seconds)' : detail.analysis ? 'Retry analysis' : 'Analyze request'}</button>}</div>
        {analysisError && <p className="error" role="alert">{analysisError} Refresh to check the saved outcome before retrying.</p>}
        {decisionError && <p className="error" role="alert">{decisionError} Review the saved state before retrying.</p>}
        {detail.analysis && <><p>Saved attempt: {detail.analysis.provider_mode === 'simulated' ? 'Simulated' : `Real Ollama ${detail.analysis.provider_model}`} · {detail.analysis.state}</p>
          {detail.analysis.error_code && <p role="alert">Analysis failed: {detail.analysis.error_code}. No tasks were created.</p>}
          <p>Analysis ID: {detail.analysis.id}</p>
          {detail.analysis.decided_at && <p>Human decision recorded: {date(detail.analysis.decided_at)}</p>}
          {detail.analysis.rejection_reason && <p>Rejection reason: {detail.analysis.rejection_reason}</p>}
          {detail.analysis.proposal && <><p>{detail.analysis.proposal.summary}</p>
            {detail.analysis.state === 'pending' && <p>Pending human review. Suggestions are inactive until approved.</p>}
            {detail.analysis.state === 'rejected' && <p>Rejected suggestions are inactive. No tasks were created.</p>}
            <ul className="task-list">{detail.analysis.proposal.tasks.map((task, index) => <li className="task-item" key={index}><div><h3>{task.title}</h3><span className={`priority ${task.priority}`}>{task.priority} priority</span><p>{task.rationale}</p></div></li>)}</ul></>}
          {detail.analysis.state === 'pending' && <div className="form-panel">
            <p>Approve this complete suggestion set to create active tasks, or reject it with a reason.</p>
            <label htmlFor="rejection-reason">Rejection reason</label><textarea id="rejection-reason" maxLength={1000} rows={3} value={reason} onChange={event => setReason(event.target.value)} disabled={!!busy} />
            <div className="form-actions"><button className="primary" disabled={!!busy} onClick={() => void decide(detail.analysis!.id, 'approve')}>Approve suggestions</button>
              <button className="secondary" disabled={!!busy} onClick={() => void decide(detail.analysis!.id, 'reject')}>Reject suggestions</button></div>
          </div>}
        </>}
      </section>
      <section className="panel"><div className="panel-heading"><div><h2>Approved tasks</h2><p>Track saved work and update its progress.</p></div><span className="count-pill">{detail.tasks.length}</span></div>
        {mutationError && <p className="error" role="alert">{mutationError} No successful update is claimed. Please retry.</p>}
        {detail.tasks.length ? <ul className="task-list">{detail.tasks.map(task => <li key={task.id} className="task-item"><div><div className="task-heading"><h3>{task.title}</h3><span className={`priority ${task.priority}`}>{task.priority} priority</span><span className={`badge ${task.state}`}>{task.state === 'done' ? 'Done' : 'Open'}</span></div><p>{task.rationale}</p></div>
          <button className="secondary" disabled={!!busy} aria-label={`${task.state === 'open' ? 'Mark done' : 'Reopen'}: ${task.title}`} onClick={() => void update(task)}>{busy === task.id ? 'Updating…' : task.state === 'open' ? 'Mark done' : 'Reopen'}</button></li>)}</ul>
          : <div className="empty"><h3>No approved tasks yet</h3><p>This request has no saved tasks. Only human-approved suggestions will become tasks.</p></div>}
      </section>
    </>}
  </>
}
