# AUREUS runtime observer policy.
# Read-only secret material required by the runtime; no secret writes, no auth management.

path "kv/data/aureus/runtime" {
  capabilities = ["read"]
}

path "kv/data/aureus/providers/vast-observer" {
  capabilities = ["read"]
}

path "kv/data/aureus/settlement/paypal-observer" {
  capabilities = ["read"]
}

path "sys/health" {
  capabilities = ["read"]
}
