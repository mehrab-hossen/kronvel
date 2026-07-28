// Hand-written mirror of backend/shared/schemas — intentionally temporary.
// Replaced by OpenAPI-generated types once `scripts/gen-types.sh` is wired up
// (Should-Have scope, deferred to a later polish pass per docs/ROADMAP.md).

export type NodeHealthStatus = "healthy" | "degraded" | "critical" | "unknown"

export interface GPUMetric {
  node: string
  gpu_index: string
  temperature_celsius: number
  utilization_percent: number
  memory_used_mib: number
  power_watts: number
  xid_error_code: number
  ecc_sbe_total: number
  observed_at: string
}

export interface NodeState {
  node: string
  gpu_count: number
  health_status: NodeHealthStatus

  recovery_score: number

  cordoned: boolean
  gpus: GPUMetric[]
  updated_at: string
}

export type AnomalyType = "thermal" | "xid_error" | "ecc_error" | "utilization" | "unknown"
export type AnomalySeverity = "low" | "medium" | "high" | "critical"

export interface Anomaly {
  node: string
  gpu_index: string
  anomaly_type: AnomalyType
  severity: AnomalySeverity
  metric_value: number
  threshold: number
  description: string
  detected_at: string
}

export interface ActionAudit {
  id: string
  action: string
  node: string
  requested_by: string
  dry_run: boolean
  policy_decision: string
  policy_risk_level: string
  policy_reason: string
  executed: boolean
  result: Record<string, unknown> | null
  error: string | null
  created_at: string
}
