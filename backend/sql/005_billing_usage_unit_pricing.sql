ALTER TABLE plan_definitions
ADD COLUMN IF NOT EXISTS usage_unit_price_cents INTEGER NOT NULL DEFAULT 100;

UPDATE plan_definitions
SET usage_unit_price_cents = CASE plan_id
  WHEN 'starter' THEN 100
  WHEN 'growth' THEN 80
  WHEN 'enterprise' THEN 50
  ELSE usage_unit_price_cents
END;
