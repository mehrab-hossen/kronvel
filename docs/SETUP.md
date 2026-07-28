# Kronvel — Setup Guide

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Docker + Docker Compose | Latest stable | Required for full local stack |
| Python | 3.11+ | Backend + simulator |
| Node.js | 18+ | Frontend |
| make | Any | Convenience commands |
| kind or minikube | Latest | Required for `kubectl` agent tool — see [Kubernetes Setup](#kubernetes-setup) |

## 1. Clone & Configure

```bash
git clone https://github.com/kaziakil/kronvel.git
cd kronvel
cp .env.example .env
```

Edit `.env` and fill in:
- `LLM_API_KEY` — API key for your configured LLM provider (e.g., Anthropic, OpenAI, Google Gemini, OpenRouter, or another supported provider)
- `LLM_PROVIDER` — Select the LLM provider to use (e.g., `anthropic`, `openai`, `gemini`, `openrouter`)
- Leave `DRY_RUN_DEFAULT=true` unless you specifically intend to test live cluster actions

## 2. Full Stack via Docker Compose (Recommended)

```bash
make dev
```

Equivalent to:

```bash
docker compose -f infra/docker-compose.yml up --build
```

This starts: backend, simulator, Prometheus, Redis, Postgres, frontend.

| Service | Local URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Backend docs (Swagger) | http://localhost:8000/docs |
| Prometheus UI | http://localhost:9090 |
| Simulator `/metrics` | http://localhost:9400/metrics |

## 3. Manual Service-by-Service Setup

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Simulator

```bash
cd simulator
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python dcgm_sim.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Prometheus (local, non-Docker)

```bash
cd infra/prometheus
prometheus --config.file=prometheus.yml
```

## 4. Kubernetes Setup

The `kubectl` agent tool requires a reachable cluster. For local development, use `kind` or `minikube` — do not point this at a production cluster during development.

```bash
kind create cluster --name kronvel-dev
kubectl create serviceaccount kronvel-agent
# Apply a scoped Role/RoleBinding — see backend/app/agents/tools/kubectl.py for required verbs
export KUBE_CONFIG=$(kind get kubeconfig --name kronvel-dev)
```

Verify connectivity:

```bash
kubectl --kubeconfig=$KUBE_CONFIG get nodes
```

## 5. Database Setup

Postgres and Redis are provisioned automatically by `docker-compose.yml` for local development. To run migrations manually:

```bash
cd backend
alembic upgrade head   # if/when Alembic migrations are introduced
```

## 6. Verify Everything Works

```bash
curl http://localhost:8000/health
```

Expected: `200 OK` with live Redis and Postgres connectivity confirmed in the response body.

```bash
make test
```

Expected: backend and frontend test suites pass.

## 7. Demo Mode

```bash
make demo
```

Runs `docker-compose.demo.yml` (faster polling interval, seeded data) and executes `scripts/demo_scenario.py`, which triggers a scripted fault → detection → remediation → audit sequence end-to-end.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `/health` fails on Postgres check | Postgres container not ready | Wait for healthcheck, or check `DATABASE_URL` in `.env` |
| Simulator metrics not appearing in Prometheus | Scrape target misconfigured | Check `infra/prometheus/prometheus.yml` target matches simulator's exposed port |
| Copilot chat returns errors | Missing or invalid `LLM_API_KEY`, incorrect `LLM_PROVIDER`, or provider configuration| Confirm the API key and provider settings in `.env`, then restart the backend|
| `kubectl` tool fails to connect | No reachable cluster or missing kubeconfig | Confirm `kind`/`minikube` running and `KUBE_CONFIG` set correctly |
| SSE stream doesn't update in frontend | Backend/frontend URL mismatch | Confirm `VITE_API_BASE_URL` matches backend's actual address |

For architecture context behind these components, see [`ARCHITECTURE.md`](ARCHITECTURE.md). For day-to-day workflow, see [`DEVELOPMENT.md`](DEVELOPMENT.md).
