import { getRemediationHistory } from "../../services/api"
import { usePolling } from "../../hooks/usePolling"
import { formatDhakaTime } from "../../utils/time"

export function AuditTrail() {
  const {
    data: audits,
    error,
    loading,
  } = usePolling(() => getRemediationHistory(), 3000)

  if (loading) {
    return <div className="panel">Loading audit trail…</div>
  }

  if (error) {
    return (
      <div className="panel panel--error">
        Failed to load audit trail: {error.message}
      </div>
    )
  }

  return (
    <div className="panel">
      <h2>Audit Trail</h2>

      {(audits ?? []).length === 0 ? (
        <div className="empty-state">
          No remediation actions recorded yet.
        </div>
      ) : (
        <div className="audit-scroll">
          <ul className="audit-list">
            {(audits ?? []).map((audit) => (
              <li
                key={audit.id}
                className={`audit-item audit-item--${audit.policy_decision}`}
              >
                <span className="audit-item__action">
                  {audit.action}
                </span>

                <span className="audit-item__node">
                  {audit.node}
                </span>

                <span className="audit-item__requested-by">
                  {audit.requested_by}
                </span>

                <span className="audit-item__decision">
                  {audit.policy_decision}
                </span>

                <span className="audit-item__mode">
                  {audit.dry_run ? "dry-run" : "LIVE"}
                </span>

                <span className="audit-item__executed">
                  {audit.executed ? "executed" : "not executed"}
                </span>

                <span className="audit-item__time">
                  {formatDhakaTime(audit.created_at)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}