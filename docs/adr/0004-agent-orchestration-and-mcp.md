# ADR 0004 — Bounded business graph and scoped MCP reads

Status: **Accepted for prototype design**. Owner: T03; implementation: T09–T11, T17.

## Decision

Select LangGraph for a typed, bounded graph: load immutable snapshot/profile → Sales extraction → deterministic schema/evidence validation → Coordination proposal → validation → persist pending proposal. LangGraph provides stateful orchestration primitives; use the graph without adopting a hosted platform or enabling external tracing by default. See the [official overview](https://docs.langchain.com/oss/python/langgraph/overview). The durable queue and human decision transaction remain application responsibilities in ADRs 0002–0003, rather than leaving an unbounded graph suspended for employee approval.

The **Sales Agent** extracts configured fields from supplied text, supplies bounded source excerpts for facts, represents unknowns explicitly and flags missing details. It does not invent customer facts, send messages, create quotations or set request status. The **Coordination Agent** consumes the validated extraction and same request snapshot; proposes internal tasks, rationale, nullable suggested owner/deadline and timezone/assumptions. It never activates tasks or treats suggestions as employee commitments. Use no more than two logical model nodes; validate each result in Python. Business profile/schema versions keep the core sector-neutral. Sample photovoltaic terminology is synthetic configuration, not a company rule.

## MCP boundary

Use one private MCP service with narrow schema-validated reads, initially `get_business_profile(profile_version)` and `list_assignable_staff()` returning synthetic IDs/display labels/roles only. No generic database query, file path, URL-fetch, shell, email, CRM or write tool. The orchestrator supplies the authorized context/version, not a model-chosen business identifier. The Coordination node receives only scoped staff choices; unknown IDs are rejected. Cache immutable profile data per run and cap directory response size.

Preliminary transport: MCP Streamable HTTP on the private Compose network, explicitly allowlisted origins/hosts, per-service credentials and no public route. Production transport/auth configuration must match the pinned MCP implementation/spec at build time. Separate worker and coding-review client identities; backend validates audience/scope and tool arguments independently of prompts. Do not pass through upstream tokens or let model text nominate arbitrary tools/endpoints. The server's read-only database role/views enforce its data scope. Follow [MCP security guidance](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices); no protocol security guarantee is assumed from network privacy alone.

Cap logical tool reads to the two known tools plus bounded retries within the job deadline. Errors terminate visibly or retry as classified transient; an unavailable directory can only yield unassigned owner if the schema/policy explicitly permits that fallback. It cannot fabricate a known employee.

## Alternatives, cost and verification

DeepAgents adds a higher-level harness useful for open-ended delegation but unnecessary autonomy/tool surface for two fixed stages. Plain Python functions would be smaller but provide less explicit agent-state orchestration for the course demonstration. A hosted graph platform adds service dependence and possible spend without an MVP requirement.

Benefits: visible agent responsibilities and bounded control flow; MCP can be reused for the Module 5 coding demo with its own identity. Trade-offs: schema/graph/tool versioning and protocol configuration add complexity; MCP is not needed merely for an internal Python function, but is retained for scoped-tool learning and extensibility. Costs are local worker/service resources plus separately approved live model calls. Model input and tool outputs are untrusted; escape displayed content and never interpret it as code or authority. T10/T12 verify missing facts, adversarial text, schema failures and denied tool calls using synthetic fixtures; no runtime verification exists yet.
