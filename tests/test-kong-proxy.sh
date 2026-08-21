#!/usr/bin/env bash
set -euo pipefail

host_name="$(oc get route kong-proxy -n kong -o jsonpath='{.spec.host}')"

test_path() {
  local path="$1"
  local expected="$2"
  local body
  body="$(curl -kfsS "https://${host_name}${path}")"
  [[ "${body}" == "${expected}" ]] || {
    printf 'ERROR %s: respuesta inesperada: %s\n' "${path}" "${body}" >&2
    return 1
  }
  printf 'OK %s\n' "${path}"
}

test_path "/demo" "Respuesta recibida a traves de Kong Community"
test_path "/demo2" "Segunda aplicacion publicada a traves de Kong Community"

