import { useEffect, useState } from 'react'
import { api, ApiError, setCsrf } from './api'
import { Workspace } from './Workspace'

type Identity = { handle: string; csrf_token: string }

export function App() {
  const [identity, setIdentity] = useState<Identity | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [expired, setExpired] = useState(false)
  async function checkSession() {
    setLoading(true); setError('')
    try { const value = await api<Identity>('/api/v1/auth/me'); setCsrf(value.csrf_token); setIdentity(value) }
    catch (cause) { if (!(cause instanceof ApiError && cause.status === 401)) setError('Sign-in service unavailable. Please retry.') }
    finally { setLoading(false) }
  }
  useEffect(() => {
    void checkSession()
    const expire = () => { setIdentity(null); setCsrf(''); setExpired(true); setError('') }
    window.addEventListener('session-expired', expire)
    return () => window.removeEventListener('session-expired', expire)
  }, [])
  async function logout() {
    setBusy(true); setError('')
    try { await api('/api/v1/auth/logout', 'POST'); setIdentity(null); setCsrf(''); setExpired(false) }
    catch (cause) { if (cause instanceof ApiError && cause.status === 401) { setIdentity(null); setCsrf('') }
      else setError('Sign-out unavailable. Please retry.') }
    finally { setBusy(false) }
  }
  if (loading) return <main className="auth-layout"><p role="status">Checking session…</p></main>
  if (identity) return <Workspace handle={identity.handle} logout={logout} signingOut={busy} authError={error} />
  return <main className="auth-layout"><section className="auth-card">
    <a className="brand" href="/"><span className="brand-icon">of</span> AI OfficeFlow</a>
    <p className="eyebrow">YOUR WORK, IN FLOW</p><h1>Sign in to AI OfficeFlow</h1>
    <p className="muted">A clear place for requests and the work that follows.</p>
    {expired && <p role="status" className="notice">Your session expired. Sign in again to continue.</p>}
    <form onSubmit={async event => {
      event.preventDefault(); const form = event.currentTarget; const data = new FormData(form)
      setBusy(true); setError('')
      try {
        const value = await api<Identity>('/api/v1/auth/login', 'POST', { handle: data.get('handle'), password: data.get('password') })
        setCsrf(value.csrf_token); form.reset(); setIdentity(value); setExpired(false)
      } catch (cause) { setError(cause instanceof ApiError && cause.status === 401 ? 'Sign-in failed. Check your credentials or retry later.' : 'Sign-in unavailable. Please retry.') }
      finally { setBusy(false) }
    }}>
      <label htmlFor="handle">Handle</label><input id="handle" name="handle" autoComplete="username" maxLength={40} required />
      <label htmlFor="password">Password</label><input id="password" name="password" type="password" autoComplete="current-password" maxLength={128} required />
      <button className="primary wide" disabled={busy} type="submit">{busy ? 'Signing in…' : 'Sign in'}</button>
    </form>
    {error && <div role="alert" className="error">{error} <button className="text-button" onClick={() => void checkSession()}>Retry connection</button></div>}
    <p className="fine-print">Controlled demo accounts · Synthetic data only</p>
  </section></main>
}
