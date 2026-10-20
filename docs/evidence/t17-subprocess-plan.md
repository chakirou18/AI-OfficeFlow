# Independent reviewer subprocess — prepared, awaiting approval

Historical preparation record. The subsequent freshly authorized **single**
execution succeeded: [actual process/session/material/source evidence](t17-independent-reviewer.json)
and [independent findings](t17-independent-findings.md). That approval is consumed;
this plan is not permission to execute again. Final evidence/CI review remains.

No model/reviewer ran during this preparation. At preparation time Issue #17 remained open, PR #35 draft/unmerged and the
specialized-reviewer requirement incomplete; the subsequent result above supersedes
that preparation status. Both prior
native attempts and their evidence are preserved.

## Selected supported mechanism

Installed Codex CLI remains **0.163.0**, with multi-agent enabled. This session's
exposed supervisor spawn schema lacks an `agent_type` selector. The first native
attempt returned UNSUPPORTED; the corrected attempt claimed reviewer findings
but supplied no native spawn/child identity, only an empty-recipient wait. This
does not prove universal CLI incompatibility; it does block claiming native
registered-agent execution. No third native attempt is planned.

The [official Module 5 source](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp/blob/de41e4096d8ac08db3852dfda4ce802f9ac0c0d2/05-agent-capabilities/README.md)
requires a specialized subagent with scoped context/permissions and an API review,
without prescribing one spawn API. The user authorized preparing this alternative.
The [Python supervisor](../../scripts/invoke_api_reviewer_process.py) will launch
exactly one fresh `codex exec` reviewer process using the **existing**
`api_reviewer` instructions read from `.codex/agents/api-reviewer.toml`.

This is **subprocess orchestration**, not native `spawn_agent`. Python supervises
the CLI child and returns its actual emitted review to the main coding agent.
It does not run a generic model supervisor that merely describes a reviewer.

Supported primitives: [exec/stdin/JSONL/ephemeral/read-only/user-config isolation](https://developers.openai.com/codex/cli/reference)
and [developer_instructions configuration](https://developers.openai.com/codex/config-reference).
The wrapper maps the real role's developer instructions to that supported setting;
it does not invent a direct named-agent CLI flag. No update, download, framework,
model override, provider or paid provisioning is needed.

## Boundaries

- Fresh exec in an empty temporary working directory; no fork/resume, prior
  conversation or expected findings. Task input is only the guarded synthetic
  patch; the existing role and canonical skill supply procedure. Standard CLI
  system guidance remains present.
- Native read-only, approval `never`, user config ignored, project instruction
  discovery budget zero. Shell/apps/plugins/memories/permission requests/hooks,
  browser/computer/image tools and both multi-agent backends disabled;
  `agents.enabled=false`, web search disabled. No file/application mutation,
  production access, task approval, further delegation or retries.
- Parent thread/session/tool/daemon linkage and API-key overrides removed from
  child environment; existing authenticated CLI login reused. Credentials are
  never copied, printed or committed; persistent config is unchanged.
- An existing evidence directory blocks re-execution. Timeout/failure preserves
  evidence and stops. Trusted Python writes audit files only. Temporary cleanup
  affects its own fixture directory only. Read-only is not OS-level read
  isolation; tools are disabled and task context is restricted.

## Evidence after fresh approval

Ignored `artifacts/t17-reviewer-process/` will contain the exact registration,
effective instruction text, synthetic stdin and hashes; actual executable/hash,
command, Python supervisor PID, reviewer PID, parent context ID, times and exit;
raw streamed JSONL/stderr, actual response and CLI `thread.started` session ID;
and full source hash maps before/after, including current uncommitted changes and
the registered role/skill. Original native-attempt artifacts are untouched.

Mechanical checks reject missing/duplicate sessions, parent session reuse, errors,
failed turns, observed tool/delegation items, changed source or nonzero exit.
Human assessment of substantive independent API findings remains required.
Exit 0, a role claim or mocked events do not demonstrate completion. Subprocess
PID/session evidence will never be labeled native spawn evidence.

## Actual non-invoking preparation checks

- `python -m unittest discover -s scripts/tests -p test_api_reviewer_process.py -v`:
  **5 passed**. `Popen` is mocked to fail if config-only or missing-approval paths
  attempt to launch a process. Tests cover exact instruction mapping and
  restrictions, and reject response-only, missing/multiple sessions and tool events.
- `codex ... debug prompt-input` with the prepared overrides in an empty temporary
  directory: exit 0; exact reviewer instructions present in developer-message
  input. No exec/model inference/reviewer invocation. Sanitized local diagnostic:
  `effective_reviewer_instructions_present=true`, `model_invocations=0`.
- CLI version/help/features and pinned official requirements were inspected
  without inference. `git diff --check` passed. No full suite/CI rerun is claimed
  for these local uncommitted changes.

## Historical precise authorization (consumed)

```powershell
python scripts/invoke_api_reviewer_process.py --approval-reference "User authorizes one independent read-only api_reviewer CLI subprocess for the T17 synthetic patch; no delegation or retries"
```

Authorize one execution of that Python-supervised independent CLI reviewer and
inspection/recording of genuine findings under the above boundaries. This historical approval was subsequently granted and consumed by the single
execution linked at the top; it is not an outstanding request. Merge, issue closure and T18 are outside this approval step.
