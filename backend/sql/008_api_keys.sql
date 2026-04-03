CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    workspace_id TEXT,
    name TEXT NOT NULL,
    key_prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'revoked', 'expired')),
    scopes TEXT[] NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_api_keys_project_status ON api_keys(project_id, status);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix_active ON api_keys(key_prefix, status);
CREATE INDEX IF NOT EXISTS idx_api_keys_last_used_at ON api_keys(last_used_at);
