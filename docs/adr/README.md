# Architecture decision records

Owner: [T03 / Issue #3](https://github.com/chakirou18/AI-OfficeFlow/issues/3). Scope: generic SME prototype, synthetic data only. These are design records, not implementation, deployment or purchasing evidence.

The [T03 design-review evidence](https://github.com/chakirou18/AI-OfficeFlow/issues/3#issuecomment-6269043175) records coverage, actual document checks, references and unresolved approval gates. T03 remains open for review; model/hosting selection is not claimed complete.

**Accepted for prototype design** means a preliminary engineering baseline chosen under the product owner's authorization to make reasonable choices. It does not claim separate product-owner endorsement of every technical detail. **Proposed / approval required** means the stated external-service, budget or operational choice is unresolved. Supersede decisions with a new numbered ADR and keep the history.

| ADR | Decision | State and boundary |
| --- | --- | --- |
| [0001](0001-system-stack.md) | React/TypeScript/Vite, FastAPI and modular monolith, Compose | Accepted for prototype design; no versions/dependencies installed |
| [0002](0002-persistence-and-jobs.md) | PostgreSQL relational core, revisions, transactional queue and leases | Accepted for prototype design; migrations/behavior unverified |
| [0003](0003-identity-and-approval.md) | Controlled accounts, opaque server-side sessions, RBAC and atomic human approval | Accepted for prototype design; real business roles remain provisional |
| [0004](0004-agent-orchestration-and-mcp.md) | Bounded LangGraph workflow and read-only scoped MCP | Accepted for prototype design; no tool server or agent implemented |
| [0005](0005-model-adapter-and-budgets.md) | Deterministic stub default; provider-neutral live adapter and cost reservations | Stub/adapter design accepted; live provider, model and budget require approval |
| [0006](0006-observability-and-alerting.md) | OTel Collector, Prometheus, Loki, Tempo, Grafana, Alertmanager | Local design accepted; external notification destination and fault exercise approval deferred |
| [0007](0007-delivery-hosting-and-rollback.md) | Local Compose, PR CI, automatic dev and manual production promotion | Local/release design accepted; paid public hosting, region and expenditure require approval |
| [0008](0008-tests-and-development-stages.md) | One-command test/boot contracts, staged delivery and evidence gates | Accepted for prototype design; all executable commands remain planned |
| [0009](0009-coding-agent-extension-pack.md) | Portable coding-agent package with API reviewer, workflow and guardrail | Capability design accepted; native runtime/manifest binding remains proposed for T17 |

The design can guide independently authorized local scaffold work without provider keys or paid hosting. T03 remains open until unresolved live model/hosting selections and design review have been recorded. T04's completion dependency on T03 is unchanged; independent preparation is allowed. No ADR authorizes real data, company integration, subagent invocation, an operational fault exercise or spending.
