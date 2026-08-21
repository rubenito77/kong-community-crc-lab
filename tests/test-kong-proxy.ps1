$ErrorActionPreference = "Stop"

$HostName = oc get route kong-proxy -n kong -o jsonpath='{.spec.host}'
$Tests = @(
    @{ Path = "/demo"; Expected = "Respuesta recibida a traves de Kong Community" },
    @{ Path = "/demo2"; Expected = "Segunda aplicacion publicada a traves de Kong Community" }
)

foreach ($Test in $Tests) {
    $Body = curl.exe -k -f -sS "https://$HostName$($Test.Path)"
    if ($Body -ne $Test.Expected) {
        throw "Respuesta inesperada para $($Test.Path): $Body"
    }
    Write-Host "OK $($Test.Path)" -ForegroundColor Green
}

