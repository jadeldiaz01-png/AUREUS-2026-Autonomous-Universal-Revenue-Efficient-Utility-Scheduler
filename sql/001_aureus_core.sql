CREATE TABLE IF NOT EXISTS compute_intents (
  id UUID PRIMARY KEY,
  idempotency_key TEXT NOT NULL UNIQUE,
  provider TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  state TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hardware_telemetry (
  id BIGSERIAL PRIMARY KEY,
  resource_id TEXT NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  power_watts NUMERIC NOT NULL,
  utilization_fraction NUMERIC NOT NULL,
  energy_kwh NUMERIC NOT NULL,
  evidence_sha256 TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS external_settlement_evidence (
  id BIGSERIAL PRIMARY KEY,
  provider_reference TEXT NOT NULL UNIQUE,
  destination_reference_hash TEXT NOT NULL,
  amount_usd NUMERIC NOT NULL,
  received_at TIMESTAMPTZ NOT NULL,
  verified BOOLEAN NOT NULL,
  source_sha256 TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS economic_proofs (
  id BIGSERIAL PRIMARY KEY,
  period_start TIMESTAMPTZ NOT NULL,
  period_end TIMESTAMPTZ NOT NULL,
  externally_settled_usd NUMERIC NOT NULL,
  total_attributed_costs_usd NUMERIC NOT NULL,
  verified_net_cash_settled_usd NUMERIC NOT NULL,
  proof_sha256 TEXT NOT NULL UNIQUE,
  demonstrated BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
