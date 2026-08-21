$ErrorActionPreference = "Stop"

$KongProxyHost = oc get route kong-proxy -n kong -o jsonpath='{.spec.host}'
$KongProxyUrl = "https://$KongProxyHost"

Write-Host "=== Kong ===" -ForegroundColor Cyan
helm status kong -n kong
oc get deployment,pod,service,route -n kong
oc get ingressclass kong

Write-Host "=== Aplicaciones ===" -ForegroundColor Cyan
oc get deployment,pod,service,ingress -n kong-demo

Write-Host "=== Pruebas externas ===" -ForegroundColor Cyan
curl.exe -k -f -sS "$KongProxyUrl/demo"
Write-Host ""
curl.exe -k -f -sS "$KongProxyUrl/demo2"
Write-Host ""

