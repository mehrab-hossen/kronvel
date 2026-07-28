# Kronvel — Project Dashboard

> Single source of truth for MVP progress. Update this file at the end of every work session. Links back to [`README.md`](README.md), [`docs/ROADMAP.md`](docs/ROADMAP.md), and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Project Metadata

| Field | Value |
|--------|-------|
| **Project** | Kronvel |
| **Version** | v0.1.0-dev |
| **Status** | 🚧 Active Development |
| **Last Updated** | July 24, 2026 |
| **Maintainer** | Kazi Akil Ahmed |
| **License** | Kronvel Community License 1.0 (KCL-1.0) |

---

## Overall Progress

| Metric | Value |
|---|---|
| **Overall MVP Completion** | `90%` `[██████████████████░░]`
 |
| **Current Milestone** | M7 — Deployed Demo-Ready MVP |
| **Next Milestone** | [ Future Development ] |
| **Current Focus** | M7 — Deployed Demo-Ready MVP |
| **Estimated Remaining Work** | 7 days (see [Day-by-Day Plan](#day-by-day-plan)) |
| **Blocking Issues** | None currently |

**Milestones**

| Milestone | Target Day | Status |
|---|---|---|
| M0 — Repo & Docs Foundation | Day 0 | 🟢 Complete |
| M1 — Simulator + Prometheus Live | Day 1 | 🟢 Complete |
| M2 — Backend Skeleton + Repositories | Day 2 | 🟢 Complete |
| M3 — Collection Pipeline + Anomaly Detection | Day 3 | 🟢 Complete |
| M4 — Dashboard v1 + Agent Tools | Day 4 | 🟢 Complete |
| M5 — Copilot Agent Live | Day 5 | 🟢 Complete |
| M6 — Closed-Loop Remediation + Audit Trail | Day 6 | 🟢 Complete |
| M7 — Deployed Demo-Ready MVP | Day 7 | ⚪ Not Started |

Status legend: ⚪ Not Started · 🟡 In Progress · 🟢 Complete · 🔴 Blocked

---

## Day-by-Day Plan

### Day 1 — Foundations + Simulator
- **Goal:** Simulator emitting realistic fault-injected GPU metrics; Prometheus scraping successfully.
- **Deliverables:** `simulator/`, `infra/docker-compose.yml`, Prometheus config.
- **Tasks:**
  - [x] `shared/schemas` defined
  - [x] `simulator/dcgm_sim.py` — `/metrics` endpoint
  - [x] `simulator/scenarios.py` — ≥2 fault scenarios (thermal, XID/ECC)
  - [x] `infra/docker-compose.yml` — full local stack skeleton
  - [x] Prometheus config scraping simulator
- **Estimated Duration:** 1 day
- **Dependencies:** None
- **DoD:** `docker-compose up` → Prometheus UI shows scraped metrics; ≥2 scenarios triggerable via env var.
- **Progress:** `[ ]` Not started

### Day 2 — Backend Skeleton + Repositories
- **Goal:** FastAPI boots, connects to Redis + Postgres, repository interfaces implemented.
- **Deliverables:** `core/config.py`, `repositories/`, `models/node.py`, `models/anomaly.py`, `/health` route.
- **Tasks:**
  - [x] `core/config.py`, `core/exceptions.py`
  - [x] `repositories/base.py` (Protocol/ABC)
  - [x] `redis_repository.py`, `postgres_repository.py`
  - [x] `models/node.py`, `models/anomaly.py`
  - [x] `/health` route with live connectivity checks
  - [x] Unit tests for repository CRUD
- **Estimated Duration:** 1 day
- **Dependencies:** None (parallel-safe with Day 1)
- **DoD:** `/health` returns 200 with Redis + Postgres checks; repository unit tests pass.
- **Progress:** `[ ]` Not started

### Day 3 — Collection Pipeline + Anomaly Detection (v1)
- **Goal:** Metrics collected, feature-engineered, anomaly detected, persisted.
- **Deliverables:** `pipeline/`, `ml/anomaly/`, `services/anomaly_service.py`, `/anomalies` route.
- **Tasks:**
  - [x] `pipeline/collector.py`
  - [x] `pipeline/processor.py`
  - [x] `pipeline/worker.py` (APScheduler, single replica)
  - [x] `ml/anomaly/features.py` + `detector.py` (statistical baseline)
  - [x] `services/anomaly_service.py`
  - [x] `/anomalies` route
  - [x] Measure fault-to-detection latency
- **Estimated Duration:** 1 day
- **Dependencies:** Day 1, Day 2
- **DoD:** Injected fault → detected anomaly visible via `GET /anomalies` within one polling cycle.
- **Progress:** `[ ]` Not started

### Day 4 — Frontend Dashboard (v1) + Agent Tools
- **Goal:** Visual dashboard live; agent tools built and unit-tested standalone.
- **Deliverables:** `frontend/` scaffold, dashboard components, `agents/tools/`.
- **Tasks:**
  - [x] `frontend/` Vite + React scaffold
  - [x] `components/dashboard/` node grid + anomaly timeline
  - [x] `agents/tools/prometheus.py`
  - [x] `agents/tools/node_state.py`
  - [x] `agents/tools/kubectl.py` (kind/minikube target)
  - [x] kind/minikube cluster provisioned
  - [x] Tool unit tests
- **Estimated Duration:** 1 day
- **Dependencies:** Day 3
- **DoD:** Dashboard updates within 5s of fault injection; each tool has a passing unit test.
- **Progress:** `[ ]` Not started

### Day 5 — Copilot Agent + Prompts + Policy Gate
- **Goal:** ReAct agent live, tool-calling, wrapped in policy/dry-run gate.
- **Deliverables:** `prompts/`, `agents/copilot.py`, `agents/policy.py`, `services/copilot_service.py`, chat UI.
- **Tasks:**
  - [x] `prompts/registry.py` + versioned templates
  - [x] `agents/provider.py`
  - [x] `agents/copilot.py` — ReAct loop, iteration cap + timeout
  - [x] `agents/policy.py` — risk classification
  - [x] `services/copilot_service.py`
  - [x] `/copilot/chat` SSE route
  - [x] `frontend/components/copilot/` chat UI
  - [x] SSE tested against real Vercel deploy
- **Estimated Duration:** 1 day
- **Dependencies:** Day 4
- **DoD:** Chat UI answers "why is node-3 unhealthy" with tool-grounded, non-hallucinated response.
- **Progress:** `[ ]` Not started

### Day 6 — Remediation + Audit Trail + Scheduler Scoring
- **Goal:** Closed loop — proposal → policy → dry_run → execution → audit.
- **Deliverables:** `models/action_audit.py`, `services/remediation_service.py`, `ml/scheduler/`, audit UI.
- **Tasks:**
  - [x] `models/action_audit.py`
  - [x] `postgres_repository.py` audit methods
  - [x] `services/remediation_service.py` (policy → dry_run → kubectl → audit)
  - [x] `/remediation/execute`, `/remediation/history` routes
  - [x] `ml/scheduler/scorer.py` (heuristic)
  - [x] `/scheduler/score` route
  - [x] Frontend audit trail view
  - [x] Live execution rehearsed against disposable kind cluster (cordon action)
- **Estimated Duration:** 1 day
- **Dependencies:** Day 5, Day 3
- **DoD:** Full trail visible in UI: policy score → dry_run → audit record; ≥1 live action type works against test cluster.
- **Progress:** `[ ]` Not started

### Day 7 — Polish, Deploy, Demo Script
- **Goal:** Deployed, demo scripted and rehearsed, docs finalized.
- **Deliverables:** Railway + Vercel deployments, `scripts/demo_scenario.py`, final docs.
- **Tasks:**
  - [ ] Railway deploy: backend, simulator, prometheus
  - [ ] Vercel deploy: frontend
  - [ ] Cross-service env var dry-run
  - [ ] `scripts/demo_scenario.py` finalized
  - [ ] `.github/workflows/*` basic CI
  - [ ] Full demo rehearsal (<3 min, unattended)
  - [ ] README screenshots added
- **Estimated Duration:** 1 day
- **Dependencies:** All prior days
- **DoD:** Fresh clone → `scripts/setup.sh` reproduces stack; deployed URLs work end-to-end; demo runs unattended.
- **Progress:** `[ ]` Not started

---

## Development Progress

### Repository Setup
- **Status:** 🟡 In Progress
- **Checklist:**
  - [x] Architecture blueprint finalized
  - [x] README.md drafted
  - [x] Repo scaffolded per structure
  - [x] `.gitignore`, `Makefile`, `LICENSE` added
  - [x] CI workflows added
- **Notes:** Documentation package complete as of this update.
- **Blocking Issues:** None
- **Priority:** High

### Frontend
- **Status:** ⚪ Not Started
- **Checklist:**
  - [x] Vite + React scaffold
  - [x] Dashboard components
  - [x] Copilot chat UI
  - [x] Audit trail view
  - [x] Type generation from OpenAPI
- **Notes:** —
- **Blocking Issues:** None
- **Priority:** High (Day 4+)

### Backend
- **Status:** ⚪ Not Started
- **Checklist:**
  - [x] `core/` config, exceptions, logging, security
  - [x] `repositories/` interfaces + implementations
  - [x] `services/` orchestration layer
  - [x] `models/` domain models
  - [x] API routes (thin controllers)
- **Notes:** —
- **Blocking Issues:** None
- **Priority:** Critical (Day 2+)

### AI Agents
- **Status:** ⚪ Not Started
- **Checklist:**
  - [x] `prompts/` versioned templates
  - [x] `agents/provider.py`
  - [x] `agents/copilot.py` ReAct loop
  - [x] `agents/policy.py` risk classification
  - [x] Agent tools (prometheus, kubectl, node_state, alert)
- **Notes:** Core differentiator — protect this scope over ML sophistication.
- **Blocking Issues:** Requires reachable K8s cluster (see Kubernetes Integration)
- **Priority:** Critical (Day 5+)

### ML Models
- **Status:** ⚪ Not Started
- **Checklist:**
  - [x] Anomaly detection — statistical baseline
  - [x] Anomaly detection — trained model *(Nice to Have)*
  - [x] Scheduler scoring — heuristic
  - [x] Model registry / versioning *(Nice to Have)*
- **Notes:** Baseline detector is sufficient for MVP; do not start trained model until Must-Haves are demo-ready.
- **Blocking Issues:** None
- **Priority:** Medium

### Kubernetes Integration
- **Status:** ⚪ Not Started
- **Checklist:**
  - [x] kind/minikube cluster provisioned
  - [x] Scoped ServiceAccount + RBAC allowlist
  - [x] `agents/tools/kubectl.py`
  - [x] `dry_run` gate implemented and defaulted true
  - [x] Live cordon action tested
- **Notes:** Highest infrastructure risk item in the whole roadmap — provision cluster by Day 3.
- **Blocking Issues:** None yet
- **Priority:** Critical

### Redis
- **Status:** ⚪ Not Started
- **Checklist:**
  - [ ] Railway managed instance provisioned
  - [x] `redis_repository.py` implemented
  - [ ] Hot state (node status, in-flight actions) wired
- **Notes:** —
- **Blocking Issues:** None
- **Priority:** High (Day 2)

### Prometheus
- **Status:** ⚪ Not Started
- **Checklist:**
  - [x] `infra/prometheus/prometheus.yml` configured
  - [x] Scraping simulator `/metrics`
  - [x] Backend PromQL query client (`pipeline/collector.py`)
- **Notes:** —
- **Blocking Issues:** None
- **Priority:** High (Day 1)

### Simulator
- **Status:** ⚪ Not Started
- **Checklist:**
  - [x] `/metrics` endpoint, valid exposition format
  - [x] Thermal spike scenario
  - [x] XID/ECC error scenario
  - [x] OOM scenario *(Should Have)*
  - [x] Scenario switchable via env var
- **Notes:** —
- **Blocking Issues:** None
- **Priority:** Critical (Day 1)

### Testing
- **Status:** ⚪ Not Started
- **Checklist:**
  - [x] Repository unit tests
  - [x] Agent tool unit tests
  - [x] Anomaly pipeline integration test
  - [x] Fault-to-detection latency measured
- **Notes:** —
- **Blocking Issues:** None
- **Priority:** Medium

### Deployment
- **Status:** ⚪ Not Started
- **Checklist:** *(see [Deployment Tracker](#deployment-tracker) below)*
- **Notes:** —
- **Blocking Issues:** None
- **Priority:** High (Day 7)

### Documentation
- **Status:**  🟢 Complete
- **Checklist:**
  - [x] README.md
  - [x] Project dashboard
  - [x] `docs/ARCHITECTURE.md`
  - [x] `docs/ROADMAP.md`
  - [x] `docs/SETUP.md`
  - [x] `docs/DEVELOPMENT.md`
  - [x] `docs/api.md` (generated)
- **Notes:** —
- **Blocking Issues:** None
- **Priority:** Medium

---

## Bug Tracker

### 🔴 Critical
_None currently._

### 🟠 High
_None currently._

### 🟡 Medium
_None currently._

### 🟢 Low
_None currently._

> Format when adding: `- [ ] [#issue-number] Short description — reported by X — assigned to Y`

---

## Feature Tracker

### Planned
- [x] Trained ML anomaly model + model registry
- [x] Kubernetes-native deployment of Kronvel (`deploy/k8s`, Helm)
- [x] Multi-provider LLM fallback (Anthropic + OpenAI)
- [x] OpenAPI → TS type generation in CI

### In Progress
- [x] Repository & documentation scaffolding

### Completed
- [x] Architecture blueprint
- [x] README.md
- [x] Project dashboard

### Deferred (Post-MVP)
- [x] Multi-cluster / multi-tenant support
- [x] Horizontal scaling of collection pipeline (queue-based worker)
- [x] Automated drift detection + retraining pipeline
- [x] Fine-grained RBAC beyond single ServiceAccount

---

## Deployment Tracker

| Environment | Status | Notes |
|---|---|---|
| **Local Development** (`docker-compose.yml`) | ⚪ Not Started | Full stack, standard polling interval |
| **Railway — Backend** | ⚪ Not Started | Pin to 1 replica (single-instance APScheduler) |
| **Railway — Simulator** | ⚪ Not Started | No external deps |
| **Railway — Prometheus** | ⚪ Not Started | Scrapes simulator |
| **Railway — Redis (Managed)** | ⚪ Not Started | Hot state |
| **Railway — Postgres (Managed)** | ⚪ Not Started | Audit + history |
| **Vercel — Frontend** | ⚪ Not Started | SSE tested against live deploy, not just localhost |
| **Docker (local demo stack)** | ⚪ Not Started | `docker-compose.demo.yml`, seeded + fast polling |
| **CI/CD** | ⚪ Not Started | Lint + test on push; type-drift check |
| **Production Readiness** | ⚪ Not Started | Not an MVP goal — tracked for post-MVP |

---

## Demo Checklist

### Functional Validation
- [x] Fault injection → detection → agent reasoning → remediation → audit, full loop works unattended
- [x] Dry-run path fully verified before any live-execution rehearsal
- [x] Live cordon action tested against disposable cluster
- [x] Fallback plan ready if live kubectl action fails on stage (dry-run narrative)

### UI Polish
- [x] Dashboard node grid + anomaly timeline visually clear at demo resolution
- [x] Copilot chat streaming renders smoothly
- [x] Audit trail view is the closing "trust" beat — pre-loaded and legible

### Performance
- [x] Fault-to-detection latency acceptable for a live 3-minute demo
- [x] SSE streaming verified on deployed Vercel environment
- [x] No visible lag in dashboard polling/streaming during demo

### Documentation
- [x] README finalized with real screenshots
- [x] Architecture diagram accurate to final build
- [x] `docs/api.md` reflects actual OpenAPI schema

### Deployment
- [ ] All Railway services live and healthy
- [ ] Vercel frontend live and pointed at correct backend URL
- [ ] Full cross-service env var dry-run completed

### Presentation Readiness
- [ ] Elevator pitch rehearsed (see README)
- [ ] Demo script timed under 3 minutes
- [ ] Anticipated judge objections prepared (safety/policy gate, scaling, ML sophistication)
- [ ] Backup recording available in case of live demo failure
