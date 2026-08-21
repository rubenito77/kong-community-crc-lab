#!/usr/bin/env bash
set -euo pipefail

KONG_PROXY_HOST="$(oc get route kong-proxy -n kong -o jsonpath='{.spec.host}')"
KONG_PROXY_URL="https://${KONG_PROXY_HOST}"

printf '%s\n' '=== Kong ==='
helm status kong -n kong
oc get deployment,pod,service,route -n kong
oc get ingressclass kong

printf '%s\n' '=== Aplicaciones ==='
oc get deployment,pod,service,ingress -n kong-demo

printf '%s\n' '=== Pruebas externas ==='
curl -kfsS "${KONG_PROXY_URL}/demo"
printf '\n'
curl -kfsS "${KONG_PROXY_URL}/demo2"
printf '\n'

