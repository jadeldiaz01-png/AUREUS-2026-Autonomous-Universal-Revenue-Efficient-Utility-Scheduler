# Data and evidence architecture

Operational truth is PostgreSQL. Revenue semantics are append-oriented and separate provider earnings, external settlement, telemetry and economic proofs.

Facts are stored separately from model forecasts. Provider earnings are observations; forecasts are inferences; externally reconciled transactions are settlement evidence. No probabilistic output can overwrite evidence provenance.

External destination identifiers are hashed before durable storage. Secrets are never persisted in evidence payloads.
