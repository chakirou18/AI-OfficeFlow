# Bounded reviewer tool guardrail

`python agent-hooks/review_guard.py --read-fixture` returns one pinned synthetic
patch as untrusted data. The fixed policy permits only `read_fixture`. It has no
SQL, HTTP, shell, arbitrary-path, approval or application-write tool.

`python agent-hooks/review_guard.py --demo` runs real guarded dispatch calls against
an isolated temporary sentinel. An unauthorized write and a failed policy check
are rejected before the write handler runs; the sentinel remains unchanged.
Missing, unreadable, malformed, expanded or mismatched policy fails closed.
The policy digest normalizes Git LF/CRLF checkout differences.

This is an executable **guardrail**, the Module 5 alternative to a lifecycle hook.
It protects this tool's dispatch boundary. It is not installed as a Codex native
hook and does not intercept unrelated shell commands or arbitrary Python callers.
The registered reviewer's separate no-write enforcement comes from its parent's
native read-only Codex sandbox, plus disabled shell/apps/plugins capabilities.
Neither mechanism authorizes a business decision or production mutation.
