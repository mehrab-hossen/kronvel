# Contributing to Kronvel

Thanks for your interest in contributing. Kronvel is an early-stage MVP, so process is intentionally lightweight — this document will grow as the project matures past the hackathon stage.

## License

By contributing to Kronvel, you acknowledge that this project is licensed under the **Kronvel Community License 1.0 (KCL-1.0)**.

Contributions are accepted under the terms of the KCL-1.0. By submitting a contribution, you confirm that you have the right to contribute the code and grant the Licensor the rights described in the project's `LICENSE` file.

## Before You Start

- Check [`PROJECT_DASHBOARD.md`](PROJECT_DASHBOARD.md) for current priorities and in-progress work before picking up something new.
- Check open issues to avoid duplicate work.
- For anything beyond a small fix, open an issue describing the change before starting — especially for anything touching `agents/policy.py`, `kubectl.py`, or `remediation_service.py`, where design intent matters more than usual.

## Development Setup

See [`docs/SETUP.md`](docs/SETUP.md) for full local environment instructions. Quick start:

```bash
git clone https://github.com/kaziakil/kronvel.git
cd kronvel
cp .env.example .env
make dev
```

## Branching & Commits

- Branch from `main`: `feature/<short-description>`, `fix/<short-description>`, `docs/<short-description>`.
- Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- Keep commits scoped — one logical change per commit. Squash noisy WIP commits before opening a PR.

## Code Standards

**Backend (Python):**
- Strong typing throughout — Pydantic models for all API boundaries, type hints on all function signatures.
- Routes stay thin — business logic belongs in `services/`, not `api/routes/`.
- New persistence needs go through `repositories/` interfaces (`base.py`), never a direct DB call from `services/`.
- Any new agent tool must be independently unit-testable without a live LLM call.
- Any change to `agents/policy.py` or the `dry_run` gate requires an explicit test demonstrating both the allow and block paths.

**Frontend (TypeScript/React):**
- Prefer function components + hooks.
- Types should come from the generated OpenAPI client (`scripts/gen-types.sh`) — don't hand-write types that duplicate backend schemas.

## Testing

```bash
make test
```

- New backend logic in `services/` or `ml/` requires unit tests.
- New API routes require at least one integration test.
- PRs that touch `remediation_service.py` or `policy.py` must include a test for the blocked/denied path, not just the happy path.

## Pull Requests

- Reference the related issue.
- Describe what changed and why, not just what.
- Update [`PROJECT_DASHBOARD.md`](PROJECT_DASHBOARD.md) checkboxes if your PR completes a tracked task.
- Update [`CHANGELOG.md`](CHANGELOG.md) under `[Unreleased]`.
- Keep PRs focused — large, multi-concern PRs will be asked to split.
- Ensure your contribution is compatible with the Kronvel Community License 1.0 (KCL-1.0).

## Contributor Ownership

Contributors retain the copyright to their original contributions.

By submitting a contribution, you grant the Licensor a perpetual, worldwide, non-exclusive, royalty-free, irrevocable license to use, reproduce, modify, distribute, sublicense, and incorporate your contribution into Kronvel, as described in the project's `LICENSE` file.

## Documentation

If your change affects setup, architecture, or environment variables, update the relevant file in `docs/` as part of the same PR — not as a follow-up.

## Reporting Bugs

Use the Bug Tracker section in [`PROJECT_DASHBOARD.md`](PROJECT_DASHBOARD.md) or open a GitHub issue with:
- Expected vs actual behavior
- Steps to reproduce
- Environment (local/Railway/Vercel)
- Logs or screenshots if relevant

## Security Issues

Do not open a public issue for security vulnerabilities. See [`SECURITY.md`](SECURITY.md).

## Commercial Licensing

Kronvel is distributed under the **Kronvel Community License 1.0 (KCL-1.0)**.

Organizations interested in commercial licensing, enterprise partnerships, or other commercial use should contact:

**Kazi Akil Ahmed**

📧 kaziakilahmed@gmail.com

## Code of Conduct

All contributors are expected to follow [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
