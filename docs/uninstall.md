# Desinstalación

La desinstalación elimina las aplicaciones, el release Helm y los namespaces. Es una operación destructiva.

## PowerShell

```powershell
.\scripts\powershell\uninstall-lab.ps1
```

## Linux/Bash

```bash
./scripts/bash/uninstall-lab.sh
```

## Comandos manuales

```bash
oc delete project kong-demo
helm uninstall kong -n kong
oc delete project kong
```

Validación posterior:

```bash
oc get project kong kong-demo
helm list -A
```

