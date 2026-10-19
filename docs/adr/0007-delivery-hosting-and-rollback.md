# ADR 0007 — Release environments, hosting options and rollback

Status: **Accepted for prototype design** for local Compose and release flow. **Proposed / product-owner approval required** for public hosting/vendor/region, domains, recurring spend and external credentials. Owner: T03; implementation: T05, T16, T18.

## Local and release decisions

Local deployment uses Compose with named PostgreSQL volumes, an explicit migration service, health/readiness checks and no public database ports. Keep secrets outside tracked Compose configuration and image layers. Test databases/volumes are isolated from development state. Build immutable image artifacts tagged by commit and promoted by digest; keep a release manifest tying API/worker/frontend/MCP versions and schema compatibility together.

GitHub Actions stages: every PR runs lint, types and deterministic unit/integration checks on isolated PostgreSQL; trusted main builds/publishes the reviewed release and, after tests pass, automatically deploys to **dev**. A separate **production** workflow uses manual `workflow_dispatch` with an approved tested release digest; it does not rebuild another artifact or silently deploy production after a push. GitHub documents [manual workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow) and [environment-scoped secrets/protections](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments). Verify available protections on the actual account before relying on them.

Use GitHub `dev` and `production` environments with distinct secrets, databases, app identities, cookie origins and deployment locks. Production means release-control topology, not real customer processing: both environments remain synthetic. Require explicit production initiation and, when a second authorized reviewer is available, environment review. A sole-maintainer setup must not promise independent second-person review it cannot provide. Do not execute untrusted PR code with deployment/model secrets; pin third-party actions and minimize workflow token permissions. Prefer short-lived host credentials when the selected host supports them. No CI workflow exists yet.

## Hosting alternatives and preliminary recommendation

| Option | Benefits | Costs, trade-offs and security implications |
| --- | --- | --- |
| Local Compose only (selected now) | No new service subscription, deterministic full-stack development | Not public deployment evidence; local hardware/disk/energy remain costs |
| Small EU-region VM(s) with Compose (preliminary public recommendation) | Close to local stack; worker, MCP and monitoring can run as ordinary processes/containers | Compute, persistent disks, snapshots, bandwidth, domain and maintenance; single host is not HA. Two separate dev/production VMs give better isolation; co-location needs explicit risk acceptance and separate projects/networks/volumes |
| Managed application platform plus managed PostgreSQL | Less host/backup administration, platform TLS | App/worker/database service charges, network rules, sleep/disk constraints and exporter integration need current verification; cannot assume free persistent workers |
| Serverless web + external job platform | Fine-grained scaling | More services and coordination, new billing/data surfaces, poorer parity with initial Compose target |

Do not select a vendor based on an unverified free tier. Before public provisioning, the product owner must approve provider, region, dev/production isolation, resource sizing, monthly ceiling, retention/backups and secret access. Obtain current quotes including backups/egress and monitoring storage; no monetary estimate is asserted here. TLS termination, restricted administration and backup access need host-specific review. No resources are provisioned.

## Deployment and rollback contract

Serialize releases per environment. Before schema changes, take an authorized backup and verify migration compatibility. Apply forward-compatible expand migrations as a controlled job, deploy the release, check readiness and run a synthetic browser/API smoke test. Record release, migration version and result. Worker shutdown must stop claims, finish/cancel bounded work and release leases safely.

On failed smoke/readiness, restore the prior compatible image manifest and recheck. Application rollback is not automatic database downgrade: additive migrations should keep the prior app compatible. A destructive/irreversible migration is deferred and needs a separate approved backup/restore plan; never run an unreviewed downgrade or delete volumes. If compatibility is uncertain, stop promotion, keep data intact and escalate. Rehearse backup restoration on an isolated synthetic database before claiming recovery. External provider charges/actions are not reversible through a code rollback.

T05/T16 must retain PR tests, automatic dev release, manual production release, migration, smoke and rollback/restore evidence. Hosting and live model approval remain T03 closure gates; local stub-based implementation can be prepared independently after task authorization, but does not satisfy public deployment criteria.
