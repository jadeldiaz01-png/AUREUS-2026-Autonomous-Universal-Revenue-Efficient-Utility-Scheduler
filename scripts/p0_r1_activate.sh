#!/usr/bin/env bash
set -euo pipefail

: "${AUREUS_SOURCE_SHA:?AUREUS_SOURCE_SHA is required}"
: "${AUREUS_DATABASE_URL_FILE:=/run/secrets/database_url}"
: "${AUREUS_EVIDENCE_DIR:=/run/evidence}"
: "${AUREUS_OPENBAO_PROXY_URL:=http://127.0.0.1:8100}"

case "$AUREUS_SOURCE_SHA" in
  [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ;;
  *) echo "AUREUS_SOURCE_SHA must be an exact lowercase 40-character SHA" >&2; exit 2 ;;
esac

if [[ -n "${OPENBAO_TOKEN:-}" || -n "${VAULT_TOKEN:-}" ]]; then
  echo "Static OpenBao/Vault token environment variables are forbidden" >&2
  exit 2
fi

umask 077
mkdir -p "$AUREUS_EVIDENCE_DIR"

command -v python >/dev/null
command -v kubectl >/dev/null
command -v sha256sum >/dev/null

test -r "$AUREUS_DATABASE_URL_FILE"
test "$(stat -c '%a' "$AUREUS_DATABASE_URL_FILE")" -le 600

export AUREUS_OPENBAO_PROXY_URL
export AUREUS_OPENBAO_EVIDENCE_FILE="$AUREUS_EVIDENCE_DIR/openbao.json"
python scripts/verify_openbao_identity.py

test -s "$AUREUS_EVIDENCE_DIR/pitr.json"
test -s "$AUREUS_EVIDENCE_DIR/otel-roundtrip.json"
test -s "$AUREUS_EVIDENCE_DIR/provider.json"
test -s "$AUREUS_EVIDENCE_DIR/revenue-channel.json"

export AUREUS_PITR_EVIDENCE_FILE="$AUREUS_EVIDENCE_DIR/pitr.json"
export AUREUS_OTEL_ROUNDTRIP_EVIDENCE_FILE="$AUREUS_EVIDENCE_DIR/otel-roundtrip.json"
export AUREUS_PROVIDER_EVIDENCE_FILE="$AUREUS_EVIDENCE_DIR/provider.json"
export AUREUS_REVENUE_CHANNEL_EVIDENCE_FILE="$AUREUS_EVIDENCE_DIR/revenue-channel.json"
export AUREUS_ECONOMIC_EVIDENCE_FILE="${AUREUS_ECONOMIC_EVIDENCE_FILE:-$AUREUS_EVIDENCE_DIR/economic.json}"
export AUREUS_EVIDENCE_OUTPUT="$AUREUS_EVIDENCE_DIR/production-evidence.json"

python scripts/collect_runtime_evidence.py
python scripts/certify_production_evidence.py \
  "$AUREUS_EVIDENCE_DIR/production-evidence.json" \
  "$AUREUS_SOURCE_SHA" \
  "$AUREUS_EVIDENCE_DIR/production-certificate.json"

for artifact in openbao.json pitr.json otel-roundtrip.json provider.json production-evidence.json production-certificate.json; do
  test -s "$AUREUS_EVIDENCE_DIR/$artifact"
  sha256sum "$AUREUS_EVIDENCE_DIR/$artifact"
done

echo "AUREUS_P0_R1=PASS source_sha=$AUREUS_SOURCE_SHA"
