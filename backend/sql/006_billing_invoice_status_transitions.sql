CREATE TABLE IF NOT EXISTS invoice_status_transitions (
  id TEXT PRIMARY KEY,
  invoice_id TEXT NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
  from_status TEXT NOT NULL,
  to_status TEXT NOT NULL,
  changed_by TEXT NOT NULL,
  changed_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_invoice_status_transitions_invoice_id
ON invoice_status_transitions(invoice_id, changed_at DESC);
