vault {
  address = "https://openbao.openbao.svc:8200"
  retry {
    num_retries = 10
  }
}

auto_auth {
  method "kubernetes" {
    mount_path = "auth/kubernetes"
    config = {
      role = "aureus-runtime-observer"
      token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    }
  }
}

# Local-only proxy: requests are authenticated with the renewable Auto-Auth token.
# The application never receives or stores a static OpenBao token.
api_proxy {
  use_auto_auth_token = "force"
}

listener "tcp" {
  address = "127.0.0.1:8100"
  tls_disable = true
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
