import type { AnomalySeverity, NodeHealthStatus } from "../../types/api"

const HEALTH_COLORS: Record<NodeHealthStatus, string> = {
  healthy: "var(--healthy)",
  degraded: "var(--degraded)",
  critical: "var(--critical)",
  unknown: "var(--unknown)",
}

const SEVERITY_COLORS: Record<AnomalySeverity, string> = {
  low: "var(--unknown)",
  medium: "var(--degraded)",
  high: "var(--degraded)",
  critical: "var(--critical)",
}

export function HealthBadge({ status }: { status: NodeHealthStatus }) {
  return (
    <span style={{ color: HEALTH_COLORS[status] }} className="badge">
      ● {status}
    </span>
  )
}

export function SeverityBadge({ severity }: { severity: AnomalySeverity }) {
  return (
    <span style={{ color: SEVERITY_COLORS[severity] }} className="badge">
      {severity.toUpperCase()}
    </span>
  )
}
