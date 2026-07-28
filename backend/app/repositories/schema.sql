CREATE TABLE IF NOT EXISTS nodes (
    node        TEXT PRIMARY KEY,
    gpu_count   INTEGER NOT NULL,
    health_status TEXT NOT NULL DEFAULT 'unknown',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS anomalies (
    id            SERIAL PRIMARY KEY,
    node          TEXT NOT NULL,
    gpu_index     TEXT NOT NULL,
    anomaly_type  TEXT NOT NULL,
    severity      TEXT NOT NULL,
    metric_value  DOUBLE PRECISION NOT NULL,
    threshold     DOUBLE PRECISION NOT NULL,
    description   TEXT NOT NULL,
    detected_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_anomalies_node ON anomalies (node);
CREATE INDEX IF NOT EXISTS idx_anomalies_detected_at ON anomalies (detected_at DESC);

-- action_audit table is added Day 6 alongside the remediation service.

CREATE TABLE IF NOT EXISTS action_audit (
    id                TEXT PRIMARY KEY,
    action            TEXT NOT NULL,
    node              TEXT NOT NULL,
    requested_by      TEXT NOT NULL DEFAULT 'operator',
    dry_run           BOOLEAN NOT NULL,
    policy_decision   TEXT NOT NULL,
    policy_risk_level TEXT NOT NULL,
    policy_reason     TEXT NOT NULL,
    executed          BOOLEAN NOT NULL DEFAULT false,
    result            JSONB,
    error             TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS node_remediation_state (
    node         TEXT PRIMARY KEY,
    cordoned     BOOLEAN NOT NULL DEFAULT false,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);


CREATE INDEX IF NOT EXISTS idx_action_audit_node ON action_audit (node);
CREATE INDEX IF NOT EXISTS idx_action_audit_created_at ON action_audit (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_node_remediation_updated_at ON node_remediation_state (updated_at DESC);
