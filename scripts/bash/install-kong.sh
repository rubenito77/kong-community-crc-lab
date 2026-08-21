#!/usr/bin/env bash
set -euo pipefail

KONG_NAMESPACE="kong"
CHART_VERSION="3.4.1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

oc apply -f "${REPO_ROOT}/manifests/namespaces/kong.yaml"
helm repo add kong https://charts.konghq.com --force-update
helm repo update

helm upgrade --install kong kong/kong \
  --namespace "${KONG_NAMESPACE}" \
  --version "${CHART_VERSION}" \
  --values "${REPO_ROOT}/helm/kong/values-db-less.yaml" \
  --wait \
  --timeout 10m

oc apply -f "${REPO_ROOT}/manifests/kong/route.yaml"
oc rollout status deployment/kong-kong -n "${KONG_NAMESPACE}" --timeout=5m

KONG_PROXY_HOST="$(oc get route kong-proxy -n "${KONG_NAMESPACE}" -o jsonpath='{.spec.host}')"
printf 'Kong Proxy: https://%s\n' "${KONG_PROXY_HOST}"

