import type { Anomaly, NodeState } from "../types/api"
import type { ActionAudit } from "../types/api"


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`)
  }
  return response.json() as Promise<T>
}

export async function getNodes(): Promise<NodeState[]> {
  const response = await fetch(`${API_BASE_URL}/nodes`)
  return handleResponse<NodeState[]>(response)
}

export async function getAnomalies(node?: string): Promise<Anomaly[]> {
  const url = new URL(`${API_BASE_URL}/anomalies`)
  if (node) url.searchParams.set("node", node)
  const response = await fetch(url.toString())
  return handleResponse<Anomaly[]>(response)
}

export async function executeRemediation(action: string, node: string, dryRun: boolean): Promise<ActionAudit> {
  const response = await fetch(`${API_BASE_URL}/remediation/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, node, dry_run: dryRun }),
  })
  return handleResponse<ActionAudit>(response)
}

export async function getRemediationHistory(node?: string): Promise<ActionAudit[]> {
  const url = new URL(`${API_BASE_URL}/remediation/history`)
  if (node) url.searchParams.set("node", node)
  const response = await fetch(url.toString())
  return handleResponse<ActionAudit[]>(response)
}

