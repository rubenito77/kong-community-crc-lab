$ErrorActionPreference = "Stop"

Write-Warning "Este script elimina las aplicaciones demo, Kong y ambos namespaces."
$Confirmation = Read-Host "Escriba ELIMINAR para continuar"
if ($Confirmation -cne "ELIMINAR") {
    Write-Host "Operación cancelada."
    exit 0
}

oc delete project kong-demo --ignore-not-found=true
helm uninstall kong -n kong --ignore-not-found
oc delete project kong --ignore-not-found=true

