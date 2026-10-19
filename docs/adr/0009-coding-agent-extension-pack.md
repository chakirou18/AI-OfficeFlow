# ADR 0009 — Portable Extension Pack design and runtime gate

Status: **Accepted for prototype design** for capabilities and boundaries; **Proposed** for native runtime registration/package format until T17. Owner: T03/T17. This ADR does not authorize spawning a subagent or implementing a skill now.

## Decision

Keep the [seven Module 5 requirements](../module5-checklist.md) distinct from business-agent features. Use existing AGENTS.md and permissions.md, plus a proposed reusable API-review workflow, a separately scoped API-reviewer subagent, a read-only MCP client, an executable guardrail and a small local extension package. Maintain portable Markdown capability definitions in `agent-capabilities/`, guardrail integration under `agent-hooks/`, and a package manifest/configuration under `plugins/ai-officeflow-agent-pack/` once an authorized runtime is selected.

The specialized reviewer has read-only access to the relevant issue, OpenAPI diff, specification and permitted repository context; it has no shell/database mutation or credentials. The workflow requests exact checks through authorized execution paths and returns findings with evidence to the lead/human reviewer. Runtime registration must enforce its scope; a prompt alone is insufficient. A hook intercepts forbidden actions and records a redacted denial before any effect. Reuse the business MCP service only with a distinct coding-review identity and synthetic context.

Native runtime format must be selected and compatibility verified in T17. The existing coding environment is not evidence that this proposed package is supported or installed. A later explicitly authorized specialized-subagent demo proves registration and permissions; no subagent is invoked by the current design task. The package may use an available already-authorized coding tool, but no paid runtime subscription or plugin purchase is approved. A custom agent is a permitted alternative only if a superseding ADR explains its loop, scope and equivalent demonstration.

## Alternatives, costs, security and trade-offs

Tool-specific global configuration is convenient but harder to reproduce across reviewers and may expose unrelated credentials. A repository-local portable package better records versions and scope, but still needs a supported runtime binding and real demonstration. A custom agent offers control over execution and guards at greater implementation/audit cost. Treating the Sales Agent or on-call agent as automatic proof of coding-agent extension capabilities conflates responsibilities; it is not selected.

No external service is needed for the portable documentation. Runtime inference and package validation may consume local hardware or an approved tool quota; determine that budget before a live demonstration. Do not claim the seven items complete until the package/workflow is loaded, the reviewer invoked with explicit authorization, an MCP read succeeds, a forbidden action is prevented, and the human reviews the final diff with issue-linked evidence. Secret-bearing runtime config remains untracked; fixtures and transcripts are sanitized. All executable artifacts remain absent.
