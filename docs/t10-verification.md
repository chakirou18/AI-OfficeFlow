# T10 local Ollama integration and evaluation

Status: **real proposal generation verified with CPU-only execution**; PR checks pending for the correction.
Issue: [T10 #10](https://github.com/chakirou18/AI-OfficeFlow/issues/10).
T09 dependency is merged through PR #24, main `3903d68`.
This records observed results, not awarded grading points or T11 approval.

## Implementation and bounds

`MODEL_MODE=simulated` remains the default for local startup and CI.
`MODEL_MODE=ollama` selects only the installed `llama3.2:3b` model on the
allowlisted local HTTP endpoint; unknown modes fail startup. No model downloads,
paid provider, automatic retry/fallback, model tools or task writes are implemented.
Request content enters an untrusted JSON message, separate from versioned system
instructions. Native Ollama JSON-schema output is independently validated by strict
Pydantic `proposal-v1`: bounded summary, 1-5 tasks, each with title, enum priority
and rationale; extra fields and malformed/incomplete/truncated output fail closed.

Each call has the existing persisted maximum 30-second deadline, 4096-token context,
512 output-token cap, 32768-byte HTTP response cap, fixed temperature/seed, and no
redirect/proxy-environment use. The API reserves a call before dispatch under a
PostgreSQL advisory transaction lock. At most one nonexpired real call runs across
API processes. Default allowance is 20 real attempts across persisted history;
`OLLAMA_MAX_CALLS` accepts 1-100. Failed/uncertain attempts consume allowance;
same-key replay does not. Increasing the configured total is an explicit operator
decision. Request locks and model I/O remain separate transactions. Cancellation
closes the HTTP stream; provider-side computation cancellation is not guaranteed.

Migration `0005_model_metadata` adds nullable model identity, preserving historical
simulated runs. Both modes and saved model identity are shown in the minimal UI.
Analyze/retry shows inactive pending suggestions or saved failure. No approve/reject
controls or endpoints are added. Authentication, Origin and CSRF checks remain.
Runtime errors contain sanitized codes only; prompts, provider bodies and credentials
are not logged. Synthetic evaluation reports are explicitly requested private artifacts.

## Actual local results, 2026-10-19

- Docker Desktop engine was initially stopped; `docker desktop start` restored it.
- From the API container, `host.docker.internal` resolved to `192.168.65.254`;
  `GET /api/version` returned **0.40.6**, differing from the initial supplied 0.40.1.
  No listener binding, firewall or public exposure was changed.
- Installed model: `llama3.2:3b`, digest
  `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`.
- Real evaluation used isolated PostgreSQL `officeflow_ollama_test`, a generated
  demo account, real authenticated/CSRF-protected HTTP routes in TestClient, and the
  real Docker-to-host Ollama HTTP call. It used fixture `simple` from
  [the synthetic inputs](../backend/tests/fixtures/ollama_evaluations.json).
- First attempt: **12.483 seconds**, HTTP **502**, persisted **failed/invalid_output**,
  no proposal and **zero active tasks created**. Report:
  ignored `artifacts/t10-real-evaluation.json`. Run ID
  `534a032f-f9ae-43ea-a110-7b6c3a9632a3`. No timeout occurred.
- Bounded diagnostics reproduced an incomplete `{` response with `done:false`
  despite `stream:false`. A JSON-mode diagnostic returned a provider error
  `prediction aborted, token repeat limit reached`. A tiny plain-text check also
  produced repetitive tokens. One conservative sampling/schema diagnostic still
  returned an incomplete envelope. These are genuine provider failures, not passing
  inference evidence. Experimental decoding changes were not adopted in the adapter.
  Four diagnostic calls plus the original evaluation were attempted; the diagnostic
  script was initially unable to import the app and made no call on that invocation.
- The evaluation stopped after the first failed workflow case. The additional live
  ambiguity/injection cases did **not** run. Do not claim real model quality, semantic
  injection resistance, or successful real proposal generation from mocked results.

## Checks

| Executed command | Actual result |
| --- | --- |
| `docker compose --profile test run --build --rm test` | **113 passed**, isolated real PostgreSQL, 61.39 s; includes the actual 30-second deadline test |
| `uv tool run --from ruff==0.14.0 ruff check --select E9,F backend scripts` | Passed |
| `npm.cmd --prefix frontend run lint` | Passed |
| `npm.cmd --prefix frontend run build` | TypeScript + Vite production build passed |
| `BROWSER_CHANNEL=msedge` then `python scripts/test_browser.py` | **12 passed**, 12.1 s; isolated browser database, authenticated analysis/persistence/no task creation |

The first full backend run had 112 passes and one stale readiness assertion for
`0004_analysis`; updating it to the actual migration head produced the passing run.
The 12 new evaluation fixtures cover simple/complex/ambiguous requests, injection,
markup/SQL/URL text, malformed JSON/schema, extra approval fields, provider failure,
timeout and truncation. They test the real adapter with **mocked HTTP responses**;
existing offline fixtures remain. PostgreSQL tests additionally verify real adapter
error mapping, no task creation, persisted metadata, replay, call allowance and
global reservation. These automated tests make no model calls.

## Focused diagnosis and successful correction, 2026-10-19

The same minimal host prompt returned repeated digits with the default Vulkan
runner (5.938 s, `done:true`, `done_reason:length`), but exactly `Hello` with
`num_gpu=0` (4.109 s, `done:true`, `done_reason:stop`). Runtime device diagnostics
identify the default runner as Vulkan on Radeon RX 5500M, offloading 28/29 layers;
CPU-only `/api/ps` reports zero VRAM. The identical CPU prompt also terminated
normally from Docker. This isolates the observed failure to the GPU execution path,
not host connectivity or the adapter's JSON validation. The underlying GPU/driver
defect is not diagnosed further; no upgrade, installation or model download is needed.

The smallest correction adds `num_gpu:0` to the existing bounded provider options;
`ollama-v2` identifies that configuration. Schema, temperature, seed, context/output
caps, call allowance, deadline and approval boundary are unchanged. A direct Docker
CPU schema check produced five validated tasks in 12.358 s, `done:true/stop`.
The subsequent production workflow evaluation in the separate synthetic test
database produced:

| Synthetic fixture ID | Time | HTTP/state | Validated tasks | Active tasks created |
| --- | --- | --- | --- | --- |
| simple | 10.855 s | 201 / pending | 5 | 0 |
| ambiguous | 7.059 s | 201 / pending | 3 | 0 |
| injection | 3.238 s | 201 / pending | 1 | 0 |

Each proposal was re-read from an independent PostgreSQL session and compared
with the authenticated API response. Artifact: ignored
`artifacts/t10-real-cpu-evaluation.json`; model/version/digest remain as recorded
above. The earlier failed report is preserved. Four focused diagnostic calls
(host default/CPU, Docker CPU minimal/schema) preceded these three workflow calls.
Affected adapter unit/PostgreSQL tests: **33 passed** in 6.11 s; pinned Ruff passed.
The existing 113-test and 12-browser baseline is retained; required CI will run
the full backend suite for the correction. No full local suite was redundantly rerun.

## Completion gate (initial blocker resolved)

The real schema-valid pending-proposal gate now passes within 30 seconds. Merge/close
only after required CI passes on the corrected commit and the issue evidence is
updated. CI results and PR/commit links are recorded in Issue #10. T11 is authorized
only after T10 is fully completed and merged. No later task starts before that gate.
