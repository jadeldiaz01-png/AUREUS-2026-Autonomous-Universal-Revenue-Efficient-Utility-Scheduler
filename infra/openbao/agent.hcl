auto_auth {
  method "kubernetes" {
    mount_path = "auth/kubernetes"
    config = { role = "aureus-runtime-observer" }
  }
}

template {
  destination = "/run/secrets/database_url"
  perms = "0400"
  contents = "{{ with secret \"kv/data/aureus/runtime\" }}{{ .Data.data.database_url }}{{ end }}"
  error_on_missing_key = true
}

template {
  destination = "/run/secrets/vast_api_key"
  perms = "0400"
  contents = "{{ with secret \"kv/data/aureus/providers/vast-observer\" }}{{ .Data.data.api_key }}{{ end }}"
  error_on_missing_key = true
}
