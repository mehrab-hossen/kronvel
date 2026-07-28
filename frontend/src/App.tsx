import { NodeGrid } from "./components/dashboard/NodeGrid"
import { AnomalyTimeline } from "./components/dashboard/AnomalyTimeline"
import { AuditTrail } from "./components/dashboard/AuditTrail"
import { CopilotChat } from "./components/copilot/CopilotChat"

export default function App() {
  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 20px" }}>
      {/* <header style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0 }}>Kronvel</h1>
        <p style={{ color: "var(--text-dim)", margin: "4px 0 0" }}>GPU Cluster Intelligence — live view</p>
      </header> */}
      <header
        style={{
          marginBottom: 32,
          textAlign: "center",
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: "2.5rem",
            letterSpacing: "-0.03em",
          }}
        >
          Kronvel
        </h1>

        <p
          style={{
            color: "var(--text-dim)",
            margin: "8px 0 0",
            fontSize: "1.05rem",
          }}
        >
          GPU Cluster Intelligence — live view
        </p>
      </header>
      <NodeGrid />
      <CopilotChat />
      <AnomalyTimeline />
      <AuditTrail />
      
    </div>
  )
}
