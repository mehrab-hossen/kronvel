# Kronvel — Development Guide

Day-to-day workflow reference for contributors. For initial environment setup, see [`SETUP.md`](SETUP.md). For architectural rationale, see [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Workflow

1. Check [`PROJECT_DASHBOARD.md`](../PROJECT_DASHBOARD.md) for current milestone and open tasks.
2. Branch: `feature/<short-description>` or `fix/<short-description>`.
3. Implement, following the conventions below.
4. Run `make test` before opening a PR.
5. Update `PROJECT_DASHBOARD.md` checkboxes and `CHANGELOG.md` `[Unreleased]` section as part of the same PR.

## Where Code Goes

| If you're adding... | It goes in... | Not in... |
|---|---|---|
| An API endpoint | `api/routes/` (thin — parse, call service, return) | Business logic inline in the route |
| Business/orchestration logic | `services/` | `api/routes/` or `agents/` |
| A new persistence need | `repositories/` (interface first in `base.py`) | Direct DB calls from `services/` |
| Cross-service reusable logic/schema | `shared/` | `core/` |
| Backend-only cross-cutting concern (auth, config, logging) | `core/` | `shared/` |
| A new agent tool | `agents/tools/` — must be independently unit-testable | `agents/copilot.py` directly |
| A new or edited LLM prompt | `prompts/` as a versioned template | Inline f-strings in `agents/` |
| ML inference logic | `ml/<domain>/` | `pipeline/` |
| Feature engineering shared between training and inference | `ml/<domain>/features.py`, imported by both `detector.py`/`scorer.py` and `trainer.py` | Duplicated in both places |

## Backend Conventions

- **Strong typing everywhere.** Pydantic models at every API boundary; type hints on all function signatures.
- **Routes are thin.** If a route handler has more than parse → call service → return, the logic belongs in `services/`.
- **Repository pattern is not optional.** Services depend on the `Protocol`/`ABC` in `repositories/base.py`, never on a concrete implementation. This is what makes services unit-testable with in-memory fakes.
- **Every remediation path must be `dry_run`-aware.** New action types added to `remediation_service.py` must respect `DRY_RUN_DEFAULT` and only bypass it when explicitly cleared by `agents/policy.py`.
- **Every proposed action gets an audit record**, approved or blocked — not just successful executions.

## Agent & Prompt Conventions

- New tools go in `agents/tools/`, follow the existing signature pattern, and get a standalone unit test that doesn't require a live LLM call.
- Prompts are never inline strings — add a new versioned file under `prompts/<domain>/` and load it via `prompts/registry.py`.
- The ReAct loop in `agents/copilot.py` has a hard iteration cap and timeout — do not remove or loosen these without a specific reason documented in the PR.
- Any change expanding what `agents/tools/kubectl.py` can do requires review against [`SECURITY.md`](../SECURITY.md).

## ML Conventions

- Start with the statistical baseline detector before reaching for a trained model — see [`ROADMAP.md`](ROADMAP.md) MVP scope rationale.
- If/when a trained model is introduced, it must go through `repositories/model_registry_repository.py` — no loading arbitrary files from `ml/artifacts/` directly in `detector.py`.

## Frontend Conventions

- Function components + hooks.
- Types come from the generated OpenAPI client (`scripts/gen-types.sh`) — regenerate after any backend schema change:
  ```bash
  make gen-types
  ```
- SSE consumption goes through the shared `useSSE` hook, which includes a polling fallback.

## Testing Expectations

| Change touches... | Minimum required test |
|---|---|
| `repositories/` | Unit test against test container or in-memory fake |
| `agents/tools/` | Standalone unit test, no live AI provider call |
| `services/remediation_service.py` or `agents/policy.py` | Test for both the approved AND blocked path |
| `api/routes/` | At least one integration test |
| `pipeline/` | Integration test measuring fault-to-detection latency for any timing-sensitive change |

## Common Commands

```bash
make dev          # full local stack
make test         # backend + frontend test suites
make demo         # scripted end-to-end demo scenario
make gen-types    # regenerate frontend types from backend OpenAPI schema
```

## Debugging Tips

- Backend Swagger UI (`/docs`) is the fastest way to manually exercise an endpoint without the frontend.
- Prometheus UI (`:9090`) lets you directly verify what the simulator is emitting before assuming a bug is in the backend pipeline.
- Audit records (`/remediation/history`) are the ground truth for "what did the agent actually decide and why" — check there before assuming a policy bug versus an agent reasoning bug.
- If the Copilot agent's answers seem ungrounded, check the tool-call trace in the SSE stream before suspecting the prompt — tool results not reaching the model is a more common failure mode than prompt wording.
