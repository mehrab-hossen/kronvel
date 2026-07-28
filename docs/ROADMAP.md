# Kronvel — Roadmap

Live day-by-day tracking: [`PROJECT_DASHBOARD.md`](../PROJECT_DASHBOARD.md). This document covers direction — the dashboard covers status.

## MVP Roadmap (7-Day Sprint)

| Day | Milestone | Focus |
|---|---|---|
| 1 | M1 | Simulator + Prometheus live |
| 2 | M2 | Backend skeleton + repositories |
| 3 | M3 | Collection pipeline + baseline anomaly detection |
| 4 | M4 | Dashboard v1 + agent tools |
| 5 | M5 | Copilot agent + policy gate |
| 6 | M6 | Closed-loop remediation + audit trail |
| 7 | M7 | Deployed, demo-ready |

Full day-by-day breakdown with tasks, DoD, and dependencies lives in [`PROJECT_DASHBOARD.md`](../PROJECT_DASHBOARD.md).

## MVP Scope

### Must Have
- Synthetic GPU telemetry with ≥2 fault scenarios
- Statistical baseline anomaly detection
- Real-time dashboard
- Tool-calling Copilot agent (not prompt-only)
- Policy gate with `dry_run` default
- Queryable action audit trail
- ≥1 real remediation action against a live/test cluster

### Should Have
- Heuristic scheduler scoring
- Versioned prompt templates
- OpenAPI → TypeScript type generation

### Nice to Have
- Trained ML anomaly model + model registry
- Multi-provider LLM fallback
- CI/CD auto-deploy on merge

### Deferred to Post-MVP
- Kubernetes-native deployment of Kronvel itself
- Multi-cluster / multi-tenant support
- Queue-based horizontal scaling of the collection pipeline
- Automated drift detection + retraining pipeline
- Fine-grained RBAC beyond a single scoped ServiceAccount

## Post-MVP Direction (Indicative, Not Committed)

### Phase 2 — Production Hardening
- Migrate `pipeline/worker.py` off in-process APScheduler to a queue-based worker (Celery/Redis or k8s CronJob), removing the single-replica constraint.
- Trained anomaly detection model with `model_registry_repository.py` versioning and an evaluation gate before promotion.
- Expand `agents/tools/kubectl.py` verb allowlist incrementally, each addition reviewed under [`SECURITY.md`](../SECURITY.md).
- Kronvel-on-Kubernetes: populate `deploy/k8s` and `deploy/helm`, currently reserved empty.

### Phase 3 — Enterprise Readiness
- Multi-cluster support — one Kronvel control plane observing/acting across multiple K8s clusters.
- Multi-tenant isolation — per-tenant policy configuration and audit scoping.
- Fine-grained RBAC — per-user/per-role permission scoping beyond the single ServiceAccount model.
- SSO/enterprise auth integration.

### Phase 4 — Platform Expansion
- Additional agent tools (cost optimization recommendations, capacity planning).
- Drift detection + automated retraining pipeline for ML components.
- Public API / webhook integrations for third-party alerting and ticketing systems.

## Explicitly Out of Scope for MVP

These are named here so they are never accidentally started under demo-week time pressure — see [`PROJECT_DASHBOARD.md`](../PROJECT_DASHBOARD.md) Risks:

- Any Kubernetes manifest/Helm chart work for deploying Kronvel itself
- A trained ML model before all Must-Have features are demo-ready
- Any RBAC model beyond one scoped ServiceAccount
