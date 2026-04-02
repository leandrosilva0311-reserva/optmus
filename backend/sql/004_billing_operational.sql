CREATE UNIQUE INDEX IF NOT EXISTS idx_invoices_project_period_unique
ON invoices(project_id, period_start, period_end);

CREATE TABLE IF NOT EXISTS billing_cycle_closures (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  invoice_id TEXT NOT NULL REFERENCES invoices(id) ON DELETE RESTRICT,
  usage_units INTEGER NOT NULL,
  closed_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  UNIQUE(project_id, period_start, period_end)
);
