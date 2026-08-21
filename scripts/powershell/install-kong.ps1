$ErrorActionPreference = "Stop"

$KongNamespace = "kong"
$ChartVersion = "3.4.1"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ValuesFile = Join-Path $RepoRoot "helm\kong\values-db-less.yaml"
$NamespaceFile = Join-Path $RepoRoot "manifests\namespaces\kong.yaml"
$RouteFile = Join-Path $RepoRoot "manifests\kong\route.yaml"

oc apply -f $NamespaceFile
helm repo add kong https://charts.konghq.com --force-update
helm repo update

helm upgrade --install kong kong/kong `
  --namespace $KongNamespace `
  --version $ChartVersion `
  --values $ValuesFile `
  --wait `
  --timeout 10m

oc apply -f $RouteFile
oc rollout status deployment/kong-kong -n $KongNamespace --timeout=5m

$KongProxyHost = oc get route kong-proxy -n $KongNamespace -o jsonpath='{.spec.host}'
Write-Host "Kong Proxy: https://$KongProxyHost" -ForegroundColor Green

