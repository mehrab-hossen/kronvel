import { getNodes } from "../../services/api"
import { usePolling } from "../../hooks/usePolling"
import { NodeCard } from "./NodeCard"

export function NodeGrid() {
  const { data: nodes, error, loading } = usePolling(getNodes, 3000)

  if (loading) return <div className="panel">Loading cluster state…</div>
  if (error) return <div className="panel panel--error">Failed to load nodes: {error.message}</div>

  return (
    <div className="panel">
      <h2>Cluster Nodes</h2>
      <div className="node-grid">
        {(nodes ?? []).map((node) => (
          <NodeCard key={node.node} node={node} />
        ))}
      </div>
    </div>
  )
}
