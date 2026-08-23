-- Execute as migration/owner role, never as application runtime.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='aureus_runtime') THEN
    CREATE ROLE aureus_runtime NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
  END IF;
END $$;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO aureus_runtime;
GRANT SELECT, INSERT, UPDATE ON compute_intents TO aureus_runtime;
GRANT SELECT, INSERT ON hardware_telemetry, external_settlement_evidence, economic_proofs TO aureus_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO aureus_runtime;
