CREATE TABLE IF NOT EXISTS plan_definitions (
  plan_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  daily_scenario_limit INTEGER NOT NULL,
  monthly_price_cents INTEGER NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscriptions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  plan_id TEXT NOT NULL REFERENCES plan_definitions(plan_id),
  status TEXT NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  renews_at TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS usage_events (
  id BIGSERIAL PRIMARY KEY,
  project_id TEXT NOT NULL,
  plan_id TEXT NOT NULL,
  scenario_id TEXT NOT NULL,
  units INTEGER NOT NULL,
  event_date DATE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS usage_daily_counters (
  project_id TEXT NOT NULL,
  plan_id TEXT NOT NULL,
  event_date DATE NOT NULL,
  consumed_units INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (project_id, plan_id, event_date)
);

CREATE TABLE IF NOT EXISTS invoices (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  status TEXT NOT NULL,
  total_cents INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS invoice_items (
  id TEXT PRIMARY KEY,
  invoice_id TEXT NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
  item_type TEXT NOT NULL,
  quantity INTEGER NOT NULL,
  unit_price_cents INTEGER NOT NULL,
  total_cents INTEGER NOT NULL,
  description TEXT NOT NULL
);

INSERT INTO plan_definitions(plan_id, name, daily_scenario_limit, monthly_price_cents)
VALUES
  ('starter', 'Starter', 50, 4900),
  ('growth', 'Growth', 250, 19900),
  ('enterprise', 'Enterprise', 2000, 99900)
ON CONFLICT (plan_id) DO NOTHING;
