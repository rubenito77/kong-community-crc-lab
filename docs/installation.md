# Instalación

## Prerrequisitos

- CRC/OpenShift operativo.
- Sesión autenticada mediante `oc`.
- Helm 3 disponible.
- Permisos para crear namespaces y recursos.
- Resolución de `*.apps-crc.testing`.

## PowerShell

```powershell
.\scripts\powershell\install-kong.ps1
.\scripts\powershell\deploy-demo-apps.ps1
```

## Linux/Bash

```bash
chmod +x scripts/bash/*.sh tests/*.sh
./scripts/bash/install-kong.sh
./scripts/bash/deploy-demo-apps.sh
```

## Instalación manual de Kong

```bash
oc apply -f manifests/namespaces/kong.yaml
helm repo add kong https://charts.konghq.com --force-update
helm repo update
helm upgrade --install kong kong/kong \
  --namespace kong \
  --version 3.4.1 \
  --values helm/kong/values-db-less.yaml \
  --wait \
  --timeout 10m
oc apply -f manifests/kong/route.yaml
```

Los scripts son idempotentes: `helm upgrade --install` y `oc apply` pueden volver a ejecutarse para reconciliar el estado declarado.

