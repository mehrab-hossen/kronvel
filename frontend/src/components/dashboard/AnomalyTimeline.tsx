import { getAnomalies } from "../../services/api"
import { usePolling } from "../../hooks/usePolling"
import { SeverityBadge } from "../shared/StatusBadge"

import { formatDhakaTime } from "../../utils/time"

export function AnomalyTimeline() {
  const { data: anomalies, error, loading } = usePolling(() => getAnomalies(), 3000)

  if (loading) return <div className="panel">Loading anomalies…</div>
  if (error) return <div className="panel panel--error">Failed to load anomalies: {error.message}</div>

  const sorted = [...(anomalies ?? [])].sort(
    (a, b) => new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime(),
  )

  return (
    <div className="panel">
      <h2>Anomaly Timeline</h2>
      {sorted.length === 0 && <div className="empty-state">No anomalies detected — cluster is healthy.</div>}
      <ul className="anomaly-list">
        {sorted.map((anomaly, i) => (
          <li key={`${anomaly.node}-${anomaly.detected_at}-${i}`} className="anomaly-item">
            <SeverityBadge severity={anomaly.severity} />
            <span className="anomaly-item__node">{anomaly.node}</span>
            <span className="anomaly-item__description">{anomaly.description}</span>
            <span className="anomaly-item__time">
              {formatDhakaTime(anomaly.detected_at)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
