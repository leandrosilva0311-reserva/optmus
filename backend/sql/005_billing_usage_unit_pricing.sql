ALTER TABLE plan_definitions
ADD COLUMN IF NOT EXISTS usage_unit_price_cents INTEGER NOT NULL DEFAULT 100;

-- Backfill only plans that still hold the default bootstrap value.
-- This avoids overriding custom commercial pricing already configured in production.
UPDATE plan_definitions
SET usage_unit_price_cents = CASE plan_id
  WHEN 'starter' THEN 100
  WHEN 'growth' THEN 80
  WHEN 'enterprise' THEN 50
  ELSE usage_unit_price_cents
END
WHERE usage_unit_price_cents = 100
  AND plan_id IN ('starter', 'growth', 'enterprise');
