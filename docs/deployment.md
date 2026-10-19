# T16 private release deployment

Status: implementation and local rehearsal. Automatic main deployment and manual
GitHub production promotion are **not yet demonstrated**. Do not close T16 from
image builds, request creation, a passing CI run or a manual local rehearsal.

## Architecture

Existing PR jobs Backend checks and Frontend checks stay on GitHub-hosted runners,
with no deployment credentials. A successful **push CI on this repository's main**
triggers `release.yml` using the tested SHA. It builds runtime images, runs the
actual images against isolated PostgreSQL with authenticated/CSRF/pending-analysis
smoke checks, tests backup/restore, then pushes those same images to GHCR. Only
repository-owned `@sha256` digests enter a strict release manifest. Mutable tags
are build handles only. The release workflow creates a pending GitHub deployment
request in the existing `development` environment.

An explicitly approved outbound-only local controller polls deployment requests
every 15 seconds. GitHub-hosted runners cannot contact Docker Desktop. This is
not a GitHub self-hosted runner: no inbound listener, remote checkout, downloaded
scripts or arbitrary workflow commands run on the PC. Only fixed local Python/
Compose operations are available. The controller checks bot identity, exact
payload, successful trusted-main CI, trusted publisher workflow, current main SHA,
image ownership/digests and a tested schema compatibility contract. Requests from
forks/PRs, failed/stale CI, other workflows or mutable images fail closed.

`promote.yml` is **workflow_dispatch only**, on main, using GitHub `production`.
The operator selects a successful development deployment ID. The exact same
manifest/digests are requested, never rebuilt; the controller also requires them
to equal its currently verified development release. No deployment secrets are
available in PR jobs. No GitHub environment success is reported until local
health, migrations and authenticated smoke actually pass. A request is not proof
of deployment. Interrupted in-progress requests require maintainer inspection;
they are not automatically retried. Both environments currently have no required
reviewers; production is still manually dispatched, never automatic.

## Private environments and safety

`infra/deployment/compose.yaml` uses separate projects `officeflow-development`
and `officeflow-production`, private networks, named database volumes and random
passwords. Frontends bind only `127.0.0.1:18080` and `127.0.0.1:28080`; APIs and
databases have no host ports. Production here means a **local synthetic release
environment**, not a public production service. Local HTTP explicitly uses
non-Secure cookies; public use requires separate approved HTTPS configuration.
No public service exposure is authorized or configured.

The existing private Collector joins each release network; release APIs never
join the core network, avoiding shared `api`/`db` DNS aliases. Stored telemetry
keeps low-cardinality development/production labels. All on-call/fault gates are
disabled, and no operational repair credentials are mounted in release APIs.
Model mode remains visibly simulated. The existing core stack/Ollama is unchanged.

Credentials, backups, demo access and release state live in ignored
`artifacts/deployment/<environment>/`. `private.json` and `demo-login.json` contain
secrets; do not print, upload or commit them. Each deployment's authenticated smoke
creates synthetic inactive suggestions, never approves tasks. Read demo access
locally from the private file; there is no public signup.

Current compatible revision is explicitly `0006_human_decisions`. No new database
migration is introduced. Future additive migrations need an updated compatibility
contract with real rollback evidence. Upgrades back up the existing environment;
failed health/smoke rolls back API/frontend only when the previous image accepts
the actual database revision. No automatic downgrade, database restore over live
data or volume deletion exists. `rollback` uses the stored previous immutable
images and verifies health/auth again. Backups use `pg_dump -Fc`; restore smoke
uses a fresh no-network PostgreSQL tmpfs container and compares request/task/run
counts and migration revision, then stops only that scratch container.

## Commands and activation gate

Local preparation/rehearsal is authorized by T16; it does not activate a controller
or publish any image. A local manifest may use exact image configuration IDs
(`sha256:...`) with null workflow IDs and `--local-rehearsal`; these are explicitly
**not registry digests or hosted-CI attestations**. The real controller rejects them.

```powershell
python scripts/deployment.py apply development --release artifacts/development-release.json --local-rehearsal
python scripts/deployment.py apply production --release artifacts/development-release.json --local-rehearsal
python scripts/deployment.py restore-smoke production
python scripts/deployment.py rollback development
```

Before actual automatic delivery, obtain approval for the concrete host/controller
activation and registry login. The proposed controller runs as a bounded foreground
Python process on this Windows PC while Docker Desktop runs; no Windows service,
startup task, self-hosted runner or external host is installed. GH CLI uses the
existing local authenticated credential for deployment status API calls. Docker
needs a private GHCR read credential in its credential store; no PAT enters Git
or workflow logs. Hosted publishing uses the scoped job GITHUB_TOKEN, not a PAT.
No paid hosting or subscription is selected; GHCR's current container storage/
bandwidth policy is documented by GitHub, not a guarantee of future free usage.

After approval: `python scripts/deployment_controller.py --approved-host`.
Production: dispatch `Promote production` with a successful development deployment
ID, then wait for controller success. Record request/run IDs, actual health/auth
results and digests. Keep the PC awake for automatic deployments; this local
fallback has no availability guarantee. No public URL is claimed; record the
running authenticated local application for the permitted deployment-demo option.

Bootstrap limitation: `workflow_run`/new manual workflows must exist on the default
branch before GitHub can trigger them. With the user's “no T16 merge until all
criteria pass” rule, activation cannot be demonstrated from an unmerged draft.
Request explicit permission for a reviewed delivery-bootstrap merge while keeping
Issue #16 open; do not silently override that gate. Until then, automatic dev and
manual GitHub production evidence remain unchecked, regardless of local rehearsal.
