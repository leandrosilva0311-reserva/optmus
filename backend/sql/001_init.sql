CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS executions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  objective TEXT NOT NULL,
  agent TEXT NOT NULL,
  status TEXT NOT NULL,
  summary TEXT,
  error TEXT,
  duration_ms INTEGER,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  execution_id TEXT NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);

INSERT INTO users(id, email, password_hash, role)
VALUES ('u-admin', 'admin@optimus.local', '41e5653fc7aeb894026d6bb7b2db7f65902b454945fa8fd65a6327047b5277fb', 'admin')
ON CONFLICT (email) DO NOTHING;
