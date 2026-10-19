# Module 5 Agent Extension Pack checklist

Owner: [T17 / Issue #17](https://github.com/chakirou18/AI-OfficeFlow/issues/17), with requirements audited under [T01 / Issue #1](https://github.com/chakirou18/AI-OfficeFlow/issues/1).

Source: official [Module 5 deliverable and demo](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp/blob/de41e4096d8ac08db3852dfda4ce802f9ac0c0d2/05-agent-capabilities/README.md). Requirements were verified at pinned course commit `de41e4096d8ac08db3852dfda4ce802f9ac0c0d2`. There is **no separate graded Module 5 homework**. Carry all seven Extension Pack requirements into the final project; they are not seven additional scored rubric criteria.

Only documentation is implemented. Paths marked **proposed** below do not exist and must not be advertised as working commands, registered subagents, installed plugins, or available MCP tools.

| Requirement | Existing or proposed artifact | Responsible tasks | Demonstration and acceptance evidence | Current status |
| --- | --- | --- | --- | --- |
| One project instructions file | Existing [AGENTS.md](../AGENTS.md), linking modular specification, architecture, team, roadmap and permissions | T01, T17 | Start a task from its issue; show the agent reading AGENTS.md and relevant linked context, following scope and using only verified commands. Retain transcript and final diff. | **File verified; complete Extension Pack demonstration not yet verified.** |
| One reusable skill/workflow/command | **Proposed:** `agent-capabilities/review-api-change/SKILL.md`, an issue-based API review workflow covering specification, OpenAPI diff, access control, tests and evidence | T17, T12 | Invoke the workflow on a small synthetic API change; show repeatable steps, exact checks, useful findings, and an issue-linked review result. A prose checklist not invoked is insufficient demonstration. | **Not yet implemented or invoked.** |
| One specialized subagent | **Proposed:** `agent-capabilities/subagents/api-reviewer.md`, with chosen runtime registration/configuration, scoped context and read-only review responsibilities | T17 | With explicit user authorization for that later demo, instantiate the specialized reviewer in a separate context. It reviews an API change, reports findings and hands back evidence; show enforced tool scope. Merely naming a team role is insufficient. | **Not yet implemented, registered or invoked.** No subagent is spawned by this documentation task. |
| One MCP tool/server | **Proposed:** documented read-only MCP service in `tools/` exposing scoped `get_business_profile` and allowed staff-directory reads, plus runtime client configuration | T09, T17 | From the coding-agent Extension Pack workflow, invoke a safe read tool using synthetic business context; retain MCP request/result and demonstrate unauthorized mutation/unknown-tool refusal. Reuse of the application's MCP service requires a separate scoped coding-agent client identity. | **Not yet implemented or connected.** Business-agent tool use alone is not the planned coding-agent demo. |
| One hook or guardrail | **Proposed:** runtime-integrated guardrail under `agent-hooks/` rejecting mutations or shell execution by the read-only reviewer identity | T17, T06, T12 | Automatically intercept a deliberately denied action before execution; show refusal and absence of side effects, then a permitted read. Include deterministic verification and redacted audit output. A warning in a prompt alone is insufficient. | **Policy documented; executable guardrail not yet implemented or demonstrated.** |
| One plugin/extension package OR custom agent | **Proposed:** small local extension package in `plugins/ai-officeflow-agent-pack/` containing a supported manifest, workflow, reviewer registration and guardrail/client configuration; tool/runtime format selected in T03/T17 | T03, T17 | Load the package in a clean supported coding-agent environment, show its capabilities discovered, invoke the workflow/reviewer, and review the resulting diff. Record setup, versions, manifest and evidence. Choose this package branch; a custom agent is an alternative only if an ADR updates scope and evidence. | **Neither package nor custom-agent alternative implemented.** Existing business agents and future on-call agent are not automatically credited for this requirement. |
| One permission/security note | Existing [permissions.md](permissions.md), with later runtime-specific scopes, credential handling and guardrail behavior added | T01, T17 | Explain coding versus business versus on-call identities, allowed/denied operations and approval boundaries; demonstrate denied operations without revealing secrets. Link policy to actual guardrail and MCP configuration. | **Note verified; runtime enforcement and demo not yet verified.** |

## Planned integrated demonstration

1. Begin from a relevant public issue using synthetic data and a small API change. Confirm explicit authorization before invoking a specialized subagent; the documentation task does not grant that authorization.
2. Load the proposed package and show the agent reading AGENTS.md, specification and permissions.
3. Invoke the reusable API review workflow, which gathers the issue, contract diff and relevant checks.
4. Invoke the registered specialized reviewer with restricted tools; record its independent findings and handoff.
5. Call a permitted MCP read tool through the coding-agent identity. Show the bounded schema and sanitized result.
6. Trigger the reviewer guardrail with a denied mutation; verify no side effect and record a permitted read for comparison.
7. Run applicable implemented checks, inspect the final diff as a human, and link the transcript, versions, commands, results, commit and limitations to T17.

This sequence is a plan. No demo transcript, registration, package load, passing test, or tool invocation is claimed. Native runtime names and artifact paths may change after an ADR; the seven capability requirements remain.

## Delivery and review gates

M0 confirms requirements and existing instruction/security documents. M1–M4 establish real contracts and testable application behavior; T09 develops the scoped MCP service. M7 completes packaging, reviewer registration, the hook and the integrated demo. Prepare design work earlier where useful, but keep T17's completion dependencies T01, T10 and T11. Link final evidence from [grading-checklist.md](grading-checklist.md) and T18. Deferral of any requirement must be recorded as an unmet Extension Pack item, not as successful completion.
