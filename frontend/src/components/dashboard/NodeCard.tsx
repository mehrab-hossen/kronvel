import { useState } from "react"
import type { NodeState } from "../../types/api"
import { HealthBadge } from "../shared/StatusBadge"
import { executeRemediation } from "../../services/api"

export function NodeCard({ node }: { node: NodeState }) {
  const gpu = node.gpus[0]

  const [liveMode, setLiveMode] = useState(false)
  const [lastResult, setLastResult] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleAction(action: "cordon" | "uncordon") {
    setBusy(true)

    try {
      const audit = await executeRemediation(action, node.node, !liveMode)

      setLastResult(
        audit.executed
          ? `✓ ${action} executed live`
          : audit.error
            ? `⚠ ${audit.error ?? audit.policy_reason}`
            : `ℹ ${action} simulated (dry-run)`,
      )
      setTimeout(() => {
        setLastResult(null)
      }, 5000)
    } catch (err) {
      setLastResult(`✕ ${(err as Error).message}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className={`node-card node-card--${node.health_status}`}>
      {/* Header */}
      <div className="node-card__header">
        <div className="node-card__name">
          {node.node}
        </div>

        <div className="node-card__badges">
          <HealthBadge status={node.health_status} />

          {node.cordoned && (
            <span className="node-card__cordoned">
              Cordoned
            </span>
          )}
        </div>
      </div>

      {/* Metrics */}
      {gpu && (
        <div className="node-card__metrics">
          <div className="metric-row">
            <span>Temp</span>
            <span>{gpu.temperature_celsius.toFixed(1)}°C</span>
          </div>

          <div className="metric-row">
            <span>Util</span>
            <span>{gpu.utilization_percent.toFixed(0)}%</span>
          </div>

          <div className="metric-row">
            <span>Power</span>
            <span>{gpu.power_watts.toFixed(0)}W</span>
          </div>

          {gpu.xid_error_code > 0 && (
            <div className="node-card__alert">
              XID {gpu.xid_error_code}
            </div>
          )}

          {gpu.ecc_sbe_total > 0 && (
            <div className="node-card__alert">
              ECC errors: {gpu.ecc_sbe_total}
            </div>
          )}
        </div>
      )}

         {/* Recovery Score */}
      <div className="node-card__recovery">
        <div className="node-card__recovery-header">
          <span>Recovery Score</span>
          <span>{node.recovery_score}%</span>
        </div>

        <div className="node-card__recovery-bar">
          <div
            className="node-card__recovery-fill"
            style={{ width: `${node.recovery_score}%` }}
          />
        </div>

        <div className="node-card__recovery-status">
          {node.recovery_score === 100
            ? "Recovered"
            : "Recovering..."}
        </div>
      </div>

      <hr className="node-card__divider" />

      {/* Actions */}
      <div className="node-card__actions">
        {node.cordoned ? (
          <button
            className="node-card__button"
            disabled={busy}
            onClick={() => handleAction("uncordon")}
          >
            Uncordon
          </button>
        ) : (
          <button
            className="node-card__button"
            disabled={busy}
            onClick={() => handleAction("cordon")}
          >
            Cordon
          </button>
        )}

        <label className="node-card__live-toggle">
          <input
            type="checkbox"
            checked={liveMode}
            onChange={(e) => setLiveMode(e.target.checked)}
          />
          <span>Live execution</span>
        </label>
      </div>

      {/* Result */}
      {lastResult && (
        <div className="node-card__result">
          {lastResult}
        </div>
      )}
    </div>
  )
}