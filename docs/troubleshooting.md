# Troubleshooting

## `CreateContainerError`: executable file `-listen=:` not found

PowerShell separó incorrectamente `-listen=:5678` y Kubernetes intentó ejecutar `-listen=:` como programa.

La configuración correcta usa un ejecutable explícito y argumentos separados:

```yaml
command: ["/http-echo"]
args:
  - "-listen=:5678"
  - "-text=Respuesta recibida a traves de Kong Community"
```

## Diagnóstico de solo lectura

PowerShell:

```powershell
oc get deployment,replicaset,pod -n kong-demo -o wide
oc describe pod -n kong-demo -l app=kong-echo
oc logs deployment/kong-echo -n kong-demo --all-containers --tail=100
oc get events -n kong-demo --sort-by='.lastTimestamp' | Select-Object -Last 20
```

Linux/Bash:

```bash
oc get deployment,replicaset,pod -n kong-demo -o wide
oc describe pod -n kong-demo -l app=kong-echo
oc logs deployment/kong-echo -n kong-demo --all-containers --tail=100
oc get events -n kong-demo --sort-by='.lastTimestamp' | tail -n 20
```

## `404 no Route matched`

Antes de crear los Ingress, el 404 generado por Kong es esperado y confirma que la Route de OpenShift llega al gateway. Después de crear los Ingress, comprobar `ingressClassName: kong`, el path y el Service backend.

## PowerShell y JSON/YAML

Para contenido multilínea usar here-strings y archivos con `oc apply -f` o `oc patch --patch-file`. No copiar los prompts `PS ...>` ni `>>`.

