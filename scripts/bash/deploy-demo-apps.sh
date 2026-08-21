#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

oc apply -f "${REPO_ROOT}/manifests/namespaces/kong-demo.yaml"
oc apply -k "${REPO_ROOT}/manifests/apps/kong-echo"
oc apply -k "${REPO_ROOT}/manifests/apps/kong-echo-2"

oc rollout status deployment/kong-echo -n kong-demo --timeout=5m
oc rollout status deployment/kong-echo-2 -n kong-demo --timeout=5m
oc get deployment,pod,service,ingress -n kong-demo

