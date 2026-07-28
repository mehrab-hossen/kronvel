# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in Kronvel, please **do not open a public GitHub issue**. Instead:

1. Email the maintainer at **kaziakilahmed@gmail.com**, or use GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) feature.
2. Include a description of the vulnerability, steps to reproduce, and potential impact.
3. Allow a reasonable window for a fix before any public disclosure.

You should expect an initial response within **3–5 business days**. This is a small team/hackathon-origin project — response times may vary, but security reports are treated as highest priority regardless of current roadmap status.

## Supported Versions

| Version | Supported |
|---|---|
| `main` (pre-release/MVP) | ✅ |
| Tagged releases | Will be tracked here once `v1.0.0` ships |

## Scope & Known Risk Areas

Kronvel's architecture includes an LLM agent with **scoped, policy-gated Kubernetes cluster access**. This is the highest-sensitivity surface in the codebase. Specific areas of concern:

- **`backend/app/agents/tools/kubectl.py`** — must run under a ServiceAccount with a minimal, explicit verb/resource allowlist. Never grant cluster-admin. Any PR expanding this tool's permissions requires explicit security review, not routine approval.
- **`backend/app/agents/policy.py`** — the risk classification gate. Any change that could allow an unclassified or under-classified action to bypass the `dry_run` default is a security-relevant change.
- **`DRY_RUN_DEFAULT`** — must default to `true` in all environments except an explicitly configured live-execution demo/production context.
- **Prompt injection** — the Copilot agent processes user input and tool output as part of its reasoning loop. Treat any path where external/untrusted data reaches the LLM context (Prometheus labels, node metadata, user chat input) as a potential prompt-injection vector when reviewing changes to `agents/copilot.py` or `prompts/`.
- **Credentials** — `ANTHROPIC_API_KEY`, `DATABASE_URL`, `REDIS_URL`, and Kubernetes credentials must never be committed. All `.env` files are gitignored; only `.env.example` files with placeholder values are committed.

## Disclosure Policy

Confirmed vulnerabilities will be patched and disclosed via a GitHub Security Advisory once a fix is available. Credit will be given to reporters who wish to be acknowledged.
