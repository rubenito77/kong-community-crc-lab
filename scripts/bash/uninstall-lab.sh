#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' 'ADVERTENCIA: se eliminarán las aplicaciones demo, Kong y ambos namespaces.'
read -r -p 'Escriba ELIMINAR para continuar: ' confirmation
if [[ "${confirmation}" != "ELIMINAR" ]]; then
  printf '%s\n' 'Operación cancelada.'
  exit 0
fi

oc delete project kong-demo --ignore-not-found=true
helm uninstall kong -n kong --ignore-not-found
oc delete project kong --ignore-not-found=true

