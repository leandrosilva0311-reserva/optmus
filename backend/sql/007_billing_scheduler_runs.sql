CREATE TABLE IF NOT EXISTS billing_scheduler_runs (
  id TEXT PRIMARY KEY,
  started_at TIMESTAMPTZ NOT NULL,
  finished_at TIMESTAMPTZ NOT NULL,
  success BOOLEAN NOT NULL,
  attempts INTEGER NOT NULL,
  alert_required BOOLEAN NOT NULL,
  processed_subscriptions INTEGER NOT NULL,
  generated_invoices INTEGER NOT NULL,
  failed_subscriptions INTEGER NOT NULL,
  duration_ms INTEGER NOT NULL,
  error TEXT,
  warnings_json TEXT NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_billing_scheduler_runs_started_at
ON billing_scheduler_runs(started_at DESC);
