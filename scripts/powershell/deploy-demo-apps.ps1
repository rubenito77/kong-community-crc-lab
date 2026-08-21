$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$NamespaceFile = Join-Path $RepoRoot "manifests\namespaces\kong-demo.yaml"
$App1 = Join-Path $RepoRoot "manifests\apps\kong-echo"
$App2 = Join-Path $RepoRoot "manifests\apps\kong-echo-2"

oc apply -f $NamespaceFile
oc apply -k $App1
oc apply -k $App2

oc rollout status deployment/kong-echo -n kong-demo --timeout=5m
oc rollout status deployment/kong-echo-2 -n kong-demo --timeout=5m
oc get deployment,pod,service,ingress -n kong-demo

