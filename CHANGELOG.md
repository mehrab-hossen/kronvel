# Changelog

All notable changes to Kronvel will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/) once a `v1.0.0` release is tagged. Pre-1.0 versions may include breaking changes in minor releases.

## [Unreleased]

### Added
- Repository architecture blueprint (Part 1 & 2 of planning phase).
- README.md with full project documentation.
- PROJECT_DASHBOARD.md for MVP progress tracking.
- CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md.
- `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/SETUP.md`, `docs/DEVELOPMENT.md`.
- Custom project license: **Kronvel Community License 1.0 (KCL-1.0)**.

### Changed
- Updated project documentation to reflect the Kronvel Community License 1.0 (KCL-1.0).
- Updated README.md, CONTRIBUTING.md, and PROJECT_DASHBOARD.md for licensing consistency.

### Fixed
- N/A

---

## [0.1.0] — MVP (target)

_Not yet released. Tracked in [`PROJECT_DASHBOARD.md`](PROJECT_DASHBOARD.md)._

### Planned
- Simulator with fault-injectable synthetic GPU telemetry.
- Baseline statistical anomaly detection over live Prometheus metrics.
- Real-time dashboard (node grid + anomaly timeline).
- Tool-calling Copilot agent with versioned prompts.
- Policy-gated, dry-run-default remediation with full audit trail.
- Heuristic scheduler scoring.
- Deployed to Railway (backend, simulator, Prometheus) + Vercel (frontend).

---

### How to Update This File

- Every PR that changes user-facing or developer-facing behavior adds an entry under `[Unreleased]`.
- On each tagged release, move `[Unreleased]` entries under a new version heading with the release date.
- Categories: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
