CREATE TABLE IF NOT EXISTS subscription_plan_changes (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  from_plan_id TEXT NOT NULL,
  to_plan_id TEXT NOT NULL,
  effective_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);
