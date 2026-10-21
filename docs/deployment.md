# T16 private release deployment

Current status: T16 completed through PR #34. The chronology below preserves intermediate blockers and their later resolution. Final delivery/recovery is recorded under **Completed manual production promotion and acceptance evidence**. Docker was unavailable during the initial T18 audit; it was subsequently started for an isolated test project, which was stopped after validation. Existing T16 stacks stayed stopped during that validation. The separately authorized 2026-10-21 recovery and walkthroughs are documented under [supplementary T18 interactive walkthroughs](#supplementary-t18-interactive-walkthroughs); all six original containers were cleanly stopped afterward. Historical localhost reachability is not claimed current; see [handover](final-handover.md).

Status: **all four T16 acceptance criteria verified on 2026-10-20**. Actual
automatic private development and manual production delivery succeeded using the
same tested digests. These are local-only synthetic release environments, not
public hosting. The foreground controller was stopped after the demonstration;
apps remain running. Earlier preparation/blocker sections are historical evidence.

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
or publish any image. A local manifest may use exact local Docker image IDs
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

## Authorized bootstrap and actual delivery evidence

On 2026-10-20 the user explicitly authorized the reviewed bootstrap merge,
foreground-only local controller and private GHCR authentication. Public exposure,
paid hosting, background services/runners and volume deletion remain prohibited.
[PR #31](https://github.com/chakirou18/AI-OfficeFlow/pull/31) merged as
`49e0e786321f24231cebae286153d18b365b4afc` after both required checks passed
on reviewed head `38796670d968b2f33ef38643443f0b622175c96a`
([PR CI](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39323714031)).
Local main was fast-forwarded. Strict Backend checks/Frontend checks and
administrator enforcement were inspected and preserved.

[Main CI 39366769002](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39366769002)
passed and automatically triggered
[Release development 39366948112](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39366948112).
A triggered workflow is not deployment success. Private GHCR read authorization
was pending at that point and later completed; actual development delivery and
manual production promotion remain unverified. Issue #16 remains open.

Existing private recordings are `artifacts/t16-development.webm` and
`artifacts/t16-production.webm`, indexed by `artifacts/t16-recording.json`.
They show the previous actual local rehearsal, not the new hosted release.
`artifacts/t16-rehearsal.json` records separate credentials/databases, isolated
restore counts (development 6/0/6, production 1/0/1 for requests/tasks/runs),
schema `0006_human_decisions`, compatible rollback/forward recovery and retention
of the healthy previous release after a failed migration candidate. These
historical results are not newly executed checks or GHCR digest attestations.
Demo access instructions remain the private per-environment `demo-login.json`;
recordings and credentials are not published. Access is local-only at
`http://127.0.0.1:18080` and `http://127.0.0.1:28080`.

The release workflow subsequently **passed**, including exact-image authenticated
runtime smoke and isolated restore, and created development request `7191157555`.
This is a pending request, not a successful local deployment. Published manifest:

- API: `ghcr.io/chakirou18/ai-officeflow-api@sha256:7fdcba0d717e33e78759aa6ee9672aad447803ac900d04a40ebfc1516767bb3c`
- Frontend: `ghcr.io/chakirou18/ai-officeflow-frontend@sha256:1fbf0229fea4a9dfb0dd06b8dab21ff72449dd909d06ea174f0c6a6abaab0510`

The initial package visibility was not verified at publication time; later
inspection found public packages (see the blocker and correction below). The controller has not started; production promotion has
not been dispatched. No deployment success is claimed.

## Registry visibility blocker (2026-10-20)

GitHub CLI refresh completed and `read:packages` is now present. Authenticated
package metadata inspection unexpectedly returned `visibility: public` for both
`ai-officeflow-api` and `ai-officeflow-frontend` (created at 03:57:47Z and
03:57:51Z). This violates the user's private-only requirement; private publishing
is **not demonstrated**. The cause of the visibility change is unconfirmed.
GitHub documents that public packages cannot be made private again:
https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility

The controller remains stopped, development request `7191157555` remains pending,
and production promotion has not been dispatched. No registry deletion was performed. The earlier delete/recreate proposal is
superseded by the user-authorized non-destructive new-name correction below.
No package, Docker volume or deployment data deletion is authorized. T16 stays open.

## Verified non-destructive private package correction

The user authorized evaluating/publishing the already-tested images under new
private names and preparing a focused branch, with **no additional merge or
deployment activation**. `fix/t16-private-registry` is review-only until explicitly
approved. Existing public packages and all deployment/telemetry data are preserved.

GitHub documents that new personal packages default to private and repository
access inheritance does **not** inherit visibility. Actual registry checks confirmed
both new packages are private while linked to `chakirou18/AI-OfficeFlow`:
[GitHub package access and visibility](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility).
Authenticated immutable pulls succeeded; anonymous manifest access was denied
for both. This verifies current privacy, not a guarantee against later maintainer
visibility changes. Public copies of these same images remain publicly available;
new private names cannot retract that prior publication.

The copy used Docker tag/push of the already-tested images, **no build**, preserving
source labels. Source provenance remains the successful main CI `39366769002`,
release `39366948112`, source commit `49e0e786321f24231cebae286153d18b365b4afc`
and original deployment request `7191157555`; it is not replaced by the correction
branch's CI. Raw source/destination registry manifest bytes and their computed
SHA-256 hashes matched exactly, including all config/layer descriptors:

| Service | New private immutable reference | Image config digest |
| --- | --- | --- |
| API | `ghcr.io/chakirou18/ai-officeflow-private-api@sha256:7fdcba0d717e33e78759aa6ee9672aad447803ac900d04a40ebfc1516767bb3c` | `sha256:a2d982961468cb688b38e48421b3ba3ab5ba11101e6657cb507bd3afdff7a042` |
| Frontend | `ghcr.io/chakirou18/ai-officeflow-private-frontend@sha256:1fbf0229fea4a9dfb0dd06b8dab21ff72449dd909d06ea174f0c6a6abaab0510` | `sha256:60390adc8c5aa6e7723c53eec54c79d0132ea30b8d36fbeed59798d0dba1666a` |

Full per-layer comparisons and privacy observations are saved locally in ignored
`artifacts/t16-private-copy-proof.json`; `python artifacts/t16_copy_private.py`
completed successfully. It is a one-time fixed copy, not a deployment tool, and
refuses to overwrite pre-existing destination packages. No credentials are stored
in that script or report; authentication was passed only through captured stdin.

The correction changes only fixed image destinations and adds fail-closed private
package/repository-link checks before building/pushing, before requesting either
environment, and before controller deployment. Packages must already exist and be
private; missing/inaccessible/public/wrong-repository metadata stops the operation.
Digest selection matches the specific destination instead of assuming the first
Docker RepoDigests entry. Old public references are rejected for new deployments.
Existing fixed controller operations, trusted-main CI/workflow provenance checks,
manual production promotion, schema compatibility and rollback/database isolation
remain in place. No Compose, database or migration configuration changed.

Copy verification is **not deployment evidence**. No deployment request was edited,
no state file was rewritten, and the controller remains stopped. The pending public
request is not converted into a successful private deployment. Once a reviewed
correction is explicitly approved and merged, a fresh trusted-main CI/release must
produce a new genuine deployment request. Normal future releases still build/test
their own commit; the two copies above retain their original commit provenance.
The existing main/SHA protections are not relaxed to deploy stale images.

Validation: `python -m unittest discover -s scripts/tests -v` passed (12 tests),
including private visibility failure cases, obsolete public-reference rejection,
destination-specific digest selection, existing provenance and isolation guards.
Required PR CI remains `Backend checks` and `Frontend checks`; exact results are
recorded in Issue #16 and the correction PR. Runtime port inspection confirmed
only `127.0.0.1:18080` / `127.0.0.1:28080` are published for release services;
APIs/databases have no host ports. No new automatic dev or manual production
delivery has been demonstrated. Issue #16 stays open; T17/T18 not started.

## Actual automatic private delivery (2026-10-20)

The user authorized merging reviewed PR #32, foreground controller activation,
private GHCR authentication, automatic development and manual production delivery.
[PR #32](https://github.com/chakirou18/AI-OfficeFlow/pull/32) merged through unchanged
required checks as `a43d7ddbbc4bfcb347941371dd6a14f1334ceb36`; local main synchronized.
[Main CI 39369826860](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39369826860)
passed and automatically triggered
[Release 39370014394](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39370014394),
which passed private-package checks, exact runtime-image authenticated smoke and
isolated restore before publishing to private packages only.

New development request [7191601728](https://api.github.com/repos/chakirou18/AI-OfficeFlow/deployments/7191601728)
was automatically received by the foreground controller. GitHub recorded
`in_progress` at 04:32:29Z, then genuine `success` at 04:33:03Z after pulls,
migrations, health and authenticated smoke at `http://127.0.0.1:18080`.
CSRF enforcement, persisted simulated pending analysis and zero task activation
passed. Controller state/proof is local `artifacts/deployment/development/proof.json`.
Old public request `7191157555` was explicitly retired as inactive, never deployed.

Delivered immutable digests (distinct from the earlier no-build copy experiment):

- API: `ghcr.io/chakirou18/ai-officeflow-private-api@sha256:cd52f4991db7660097c90bed9c4516b72d8f63f3183c8ccae794dffee483731b`
- Frontend: `ghcr.io/chakirou18/ai-officeflow-private-frontend@sha256:0a5b863a22c3808e443b3b8cef3ed1c52c2c4a78178c4c7c08150f222c37acaa`

Manual [promotion 39370240008](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39370240008)
was explicitly dispatched with development ID 7191601728 but **failed before any
production request or deployment**: the new private-package metadata check requires
`packages: read`, absent from the promotion job's scoped token. The existing release
job has package write access and passed this same check. Draft
[PR #33](https://github.com/chakirou18/AI-OfficeFlow/pull/33), head
`5a5d6d6484a6a691d5df276ab7d955e15ba0d4d3`, adds exactly that read-only permission;
[required CI 39370420407](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39370420407)
passed (Backend checks 1m39s; Frontend checks 15s). Its additional bootstrap merge
exception was pending at that point and was subsequently explicitly authorized;
the successful resolution is recorded below.

Independent delivered-development recovery verification passed using
`python artifacts/t16_private_dev_recovery.py` (exit 0): isolated no-network restore
matched `7|0|7|0006_human_decisions`; compatible previous-image rollback and forward
recovery passed authenticated health/smoke and retained every pre-existing
request/task/run ID. Synthetic smoke increased counts from 7/0/7 to 9/0/9, with
zero task activation. Schema remained `0006_human_decisions`. Full proof is local
`artifacts/t16-private-dev-recovery.json`. Production was untouched by the failed
promotion. No package, volume, database or deployment data deletion occurred.

## Completed manual production promotion and acceptance evidence

The user explicitly approved the one-time PR #33 bootstrap exception.
[PR #33](https://github.com/chakirou18/AI-OfficeFlow/pull/33) merged as
`d6856b4616898d33a06cf92c45d59a1e53465493` after both required checks passed on
`5a5d6d6484a6a691d5df276ab7d955e15ba0d4d3`. Only the missing read-only package
permission changed. Strict merge checks and administrator enforcement were preserved.
[Main CI 39370966715](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39370966715)
also passed. The failed first promotion remains in history and is not counted as success.

Manual [Promote production 39370972260](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39370972260)
was dispatched on main with successful development deployment ID **7191601728**.
It reused that deployment's exact manifest and private digests listed above;
production did not rebuild either image. Production request
[7191726926](https://api.github.com/repos/chakirou18/AI-OfficeFlow/deployments/7191726926)
targeted `production` with source release commit
`a43d7ddbbc4bfcb347941371dd6a14f1334ceb36`, while the manually invoked promotion
workflow itself ran at permission-fix commit `d6856b4616898d33a06cf92c45d59a1e53465493`.
The controller verified successful trusted-main CI/publisher provenance, successful
manual workflow origin, private package ownership/visibility and equality with
its verified development state. GitHub recorded `in_progress` at 04:42:44Z and
**success at 04:43:11Z**, after actual image pulls, migrations, health and
authenticated smoke at `http://127.0.0.1:28080`. Both environments passed CSRF,
persisted simulated pending analysis and zero task activation. Running container
references and image IDs were independently compared with the promoted digests.

`python artifacts/t16_final_delivery_verify.py` completed exit 0. Actual production
restore in a fresh no-network tmpfs PostgreSQL instance matched
**3 requests / 0 tasks / 3 runs / 0006_human_decisions**. The development restore,
rollback and forward-recovery proof above applies to the same exact release and
was reused rather than rerun. All baseline row IDs survived: development 6/0/6
before delivery became 9/0/9 after deployment/recovery smoke; production 2/0/2 became
3/0/3 after promotion smoke. Separate live DB credentials were compared in memory,
not recorded; database names and volumes were independently verified as
`officeflow_development` / `officeflow-development_database` and
`officeflow_production` / `officeflow-production_database`. Prometheus, Loki, Tempo
and Grafana named volumes remain present. No package, volume or database deletion,
live restore-over, downgrade or public service exposure occurred. Existing public
GHCR packages remain untouched.

Fresh authenticated dashboard recordings were captured from the actual delivered
applications using the installed Edge browser and existing workspace encoder cache
(`PLAYWRIGHT_BROWSERS_PATH=artifacts/playwright node artifacts/t16_delivered_capture.mjs`).
The first attempt lacked that cache setting; no encoder/runtime was downloaded.
Videos show synthetic dashboard counts and pseudonymous demo handles, with no
passwords, session tokens, request descriptions or model bodies. Recorded health
returned ready/database OK and migration `0006_human_decisions` in both environments.

| Acceptance criterion | Actual evidence |
| --- | --- |
| Actual deployment recording, synthetic data and access instructions | [Development video](evidence/t16-development.webm), [production video](evidence/t16-production.webm); [development poster](evidence/t16-development.png), [production poster](evidence/t16-production.png). Start Docker Desktop, use the same PC's localhost URLs, and read that environment's ignored `artifacts/deployment/<environment>/demo-login.json` locally to sign in. Never publish that file. |
| PR tests, automatic dev and manual production of tested digests | Required [PR #32 CI](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39369153430), [PR #33 CI](https://github.com/chakirou18/AI-OfficeFlow/actions/runs/39370420407), main CI/release/manual workflow links and genuine deployment status sequences above. |
| Isolated DB/secrets and previous compatible image recovery | Independent live configuration/volume comparisons; delivered-development rollback/forward recovery retained every prior row ID; earlier failed-migration candidate rehearsal retained a healthy previous release, with the same unchanged compatibility schema. |
| Migrations and isolated backup/restore without paid provisioning | Both environments at `0006_human_decisions`; isolated development restore 7/0/7 and production restore 3/0/3. Fixed local Docker host, no paid host or subscription. |

[Sanitized machine-readable evidence](evidence/t16-delivery.json) contains the
release manifest, deployment IDs/status times, counts and recovery results.
Detailed local reports remain `artifacts/t16-final-delivery-proof.json`,
`artifacts/t16-private-dev-recovery.json` and `artifacts/t16-delivered-recording.json`.
Credentials, backups and session material remain ignored and unpublished.

The controller was intentionally stopped by operator Ctrl+C after production success;
no background service, scheduled task or self-hosted runner was installed.
The apps remain running on loopback and require this PC/Docker Desktop. Later
main commits can enqueue new release requests while the controller is stopped;
those requests are not claimed deployed by this evidence. Restarting the approved
foreground controller is required for future delivery. This evidence establishes
the completed development/production demonstration of source release `a43d7dd`,
not continuous availability, public HTTPS hosting or deployment of later docs commits.
T17/T18 remain outside this task; no final grading score is claimed.


## Supplementary T18 interactive walkthroughs

On 2026-10-21, after explicit recovery and recording authorization, the original
T16 Development and Production containers were recovered and used for two genuine
browser walkthroughs. Publication was separately authorized. These recordings
supplement the original T16 delivery videos, which remain unchanged.

| Environment | Walkthrough | Endpoint during recording | Persisted requests / analyses / active tasks |
| --- | --- | --- | --- |
| Development | [44.76-second video](evidence/t18-development-walkthrough.webm) | `http://127.0.0.1:18080` | 9 / 9 / 0 |
| Production | [44.64-second video](evidence/t18-production-walkthrough.webm) | `http://127.0.0.1:28080` | 3 / 3 / 0 |

Both environments use the tested T16 release
`a43d7ddbbc4bfcb347941371dd6a14f1334ceb36` and the exact API/frontend digests
recorded in [T16 delivery JSON](evidence/t16-delivery.json). Retained container IDs,
image identities, environment settings, separate database volumes/networks and
loopback bindings were checked before startup. These are independent persisted
databases running the same application features. The videos do not demonstrate a
new deployment, production promotion or updated application release. Automatic
development delivery and manual production promotion remain the historical T16
events identified above. No public hosting or official grading points are claimed.

Each 1280-by-720 silent video follows Overview, Requests, the Awaiting review
filter, an existing synthetic request, its saved simulated pending proposal,
System health, and a return to Overview. Visible mouse interactions operate the
real rendered application. Browser-only captions identify the verified environment
and localhost endpoint; an event-following cursor makes navigation visible.
No mock screens or artificial data differences were introduced. Only the initial
0.5 seconds of browser loading was trimmed; raw recordings remain private.

Both candidates passed full-stream decoding and complete Edge playback at 8x,
with no playback errors or dropped frames. Visual inspection covered 16 sampled
playback frames per video across every scene and full-size stage captures.
Reviewed content contains only synthetic records and pseudonymous handles, with
no credentials, tokens, private configuration or sensitive logs displayed.
Authentication occurred before recording. Business-write requests were blocked,
and before/after complete-row hashes matched for requests, analyses, tasks,
foundation checks and demo users; authorized session writes were the exception.

The legacy System health panel still says LOCAL DEVELOPMENT/T04 in both
environments. Captions explicitly identify the actual environment and legacy panel;
this wording is not evidence of a different release. Existing proposals are
simulated and inactive; no model call or approval occurred during recording.

| File | SHA-256 |
| --- | --- |
| `t18-development-walkthrough.webm` | `5e596b9a773b04d2ba84da07ced02d6cfc881650a7d4ba736fce2b2178bc68e0` |
| `t18-production-walkthrough.webm` | `d377a901506a2f95ddbec7f766bfaec1c87faff56585f56d963f9c12c753942b` |

Before recovery, retained logical dumps restored successfully in isolated,
network-disabled PostgreSQL 17.11 scratch databases, and offline copies of the
stopped original volumes were verified. Backups and private verification data stay
unpublished. Both original databases completed ordinary WAL recovery, reached
schema `0006_human_decisions`, and returned API/database readiness HTTP 200.
After recording, all six T16 containers stopped with exit code 0; both PostgreSQL
logs confirmed clean shutdown. Their volumes and original evidence were preserved.
No migration, rebuild, pull, controller activation or deployment occurred.
Localhost applications are not claimed currently available after that shutdown.
