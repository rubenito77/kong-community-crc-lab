# Pruebas de plugins con OpenShift Pipelines

## 1. Objetivo

OpenShift Pipelines ejecuta las pruebas reproducibles de los plugins de Kong
Community definidos en este repositorio. La primera Pipeline valida el plugin
`rate-limiting` sobre `/demo` y usa `/demo2` como ruta de control.

La ejecución no utiliza la Admin API de Kong. Todos los cambios se realizan por
medio de `KongPlugin` e `Ingress`, y Kong Ingress Controller actualiza Kong en
modo DB-less.

## 2. Flujo

1. Clonar la revisión indicada del repositorio público.
2. Confirmar HTTP 200 en `/demo` y `/demo2`.
3. Aplicar `KongPlugin/demo-rate-limit`.
4. Anotar solamente `Ingress/kong-echo`.
5. Enviar siete solicitudes a `/demo` desde el mismo pod.
6. Confirmar respuestas HTTP 200 y HTTP 429.
7. Confirmar que `/demo2` mantiene HTTP 200.
8. Conservar el plugin para inspección o retirarlo mediante `cleanup=true`.

Las Tasks se ejecutan en pods diferentes. El PipelineRun solicita un PVC
temporal de `100Mi` mediante `volumeClaimTemplate` para compartir el repositorio
clonado y el archivo de evidencias entre esos pods. Un workspace `emptyDir` no
sirve para este flujo porque su contenido queda limitado al pod de cada TaskRun.

El tráfico se envía al proxy interno:

```text
http://kong-kong-proxy.kong.svc.cluster.local
```

Esto evita depender del DNS externo y del certificado de la Route durante la
ejecución dentro del cluster.

## 3. Recursos

| Recurso | Namespace | Función |
|---|---|---|
| `ServiceAccount/kong-plugin-tester` | `kong-demo` | Identidad de las pruebas. |
| `Role/kong-plugin-tester` | `kong-demo` | Permisos mínimos sobre KongPlugin e Ingress. |
| `Pipeline/kong-plugin-rate-limiting` | `kong-demo` | Orquesta la prueba completa. |
| `PipelineRun/kong-plugin-rate-limiting-*` | `kong-demo` | Ejecución concreta. |
| `KongPlugin/demo-rate-limit` | `kong-demo` | Límite de cinco solicitudes por minuto e IP. |

No se concede `cluster-admin` ni acceso a Secrets. El repositorio público no
requiere credenciales Git.

## 4. Prerrequisito importante

La Pipeline clona la rama indicada y lee este archivo:

```text
manifests/plugins/rate-limiting/kongplugin.yaml
```

Por ello, los archivos de la Pipeline deben estar publicados en GitHub antes de
crear el primer `PipelineRun` contra `main`. Para probar una rama, se modifica el
parámetro `git-revision` del PipelineRun.

## 5. Instalación

### PowerShell

Desde la raíz del clon local:

```powershell
oc apply -k .\pipelines\rbac
```

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-rate-limiting.yaml
```

Validar permisos efectivos:

```powershell
oc auth can-i create kongplugins.configuration.konghq.com `
  --as=system:serviceaccount:kong-demo:kong-plugin-tester `
  -n kong-demo
```

```powershell
oc auth can-i patch ingresses.networking.k8s.io `
  --as=system:serviceaccount:kong-demo:kong-plugin-tester `
  -n kong-demo
```

### Linux

```bash
oc apply -k pipelines/rbac
oc apply -f pipelines/pipelines/kong-plugin-rate-limiting.yaml
```

```bash
oc auth can-i create kongplugins.configuration.konghq.com \
  --as=system:serviceaccount:kong-demo:kong-plugin-tester \
  -n kong-demo
```

```bash
oc auth can-i patch ingresses.networking.k8s.io \
  --as=system:serviceaccount:kong-demo:kong-plugin-tester \
  -n kong-demo
```

## 6. Ejecutar la prueba

El manifiesto usa `generateName`, por lo que cada ejecución obtiene un nombre
nuevo.

### PowerShell

```powershell
oc create -f .\pipelines\runs\rate-limiting-run.yaml
```

```powershell
$PIPELINE_RUN = oc get pipelinerun -n kong-demo `
  -l kong-lab/plugin=rate-limiting `
  --sort-by=.metadata.creationTimestamp `
  -o jsonpath='{.items[-1:].metadata.name}'
```

```powershell
Write-Host "PipelineRun: $PIPELINE_RUN"
oc wait --for=condition=Succeeded `
  "pipelinerun/$PIPELINE_RUN" `
  -n kong-demo `
  --timeout=10m
```

```powershell
tkn pipelinerun logs "$PIPELINE_RUN" -n kong-demo -f
```

Si `tkn` no está instalado:

```powershell
oc logs -n kong-demo `
  -l "tekton.dev/pipelineRun=$PIPELINE_RUN" `
  --all-containers=true `
  --prefix=true
```

### Linux

```bash
oc create -f pipelines/runs/rate-limiting-run.yaml
```

```bash
PIPELINE_RUN="$(
  oc get pipelinerun -n kong-demo \
    -l kong-lab/plugin=rate-limiting \
    --sort-by=.metadata.creationTimestamp \
    -o jsonpath='{.items[-1:].metadata.name}'
)"
```

```bash
echo "PipelineRun: ${PIPELINE_RUN}"
oc wait --for=condition=Succeeded \
  "pipelinerun/${PIPELINE_RUN}" \
  -n kong-demo \
  --timeout=10m
```

```bash
tkn pipelinerun logs "${PIPELINE_RUN}" -n kong-demo -f
```

## 7. Resultado esperado

La salida debe contener al menos:

```text
baseline /demo: HTTP 200
baseline /demo2: HTTP 200
request=1 status=200
request=6 status=429
control=/demo2 status=200
PASS: rate-limiting produjo HTTP 200 y HTTP 429; /demo2 continuo en HTTP 200
```

El instante exacto del primer `429` puede variar si ya existió tráfico desde la
misma IP durante la ventana activa. El criterio automatizado exige al menos un
HTTP 200, al menos un HTTP 429 y HTTP 200 en `/demo2`.

## 8. Inspección posterior

```powershell
oc get pipelinerun,taskrun,pod -n kong-demo `
  -l "tekton.dev/pipelineRun=$PIPELINE_RUN"
```

```powershell
oc get kongplugin demo-rate-limit -n kong-demo -o yaml
oc get ingress kong-echo -n kong-demo -o yaml
```

## 9. Limpieza

La ejecución de ejemplo usa `cleanup=false`. Después de verificar la evidencia:

```powershell
oc annotate ingress kong-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-rate-limit -n kong-demo
```

En Linux se usan los mismos comandos.

Para que una ejecución futura retire el plugin automáticamente, establecer:

```yaml
- name: cleanup
  value: "true"
```

## 10. Diagnóstico

```powershell
oc get pipelinerun "$PIPELINE_RUN" -n kong-demo -o yaml
oc get taskrun -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN"
oc get events -n kong-demo --sort-by='.lastTimestamp' | Select-Object -Last 30
```

```powershell
oc logs deployment/kong-kong -n kong -c ingress-controller --since=10m
oc logs deployment/kong-kong -n kong -c proxy --since=10m
```

### Workspace y SCC `restricted-v2`

OpenShift ejecuta los steps con un UID dinámico. La tarea de clonación define
`HOME=/tekton/home` y registra `/workspace/source` como `safe.directory` de Git.
Esto evita que Git rechace el workspace compartido por diferencias de propiedad:

```text
fatal: detected dubious ownership in repository at '/workspace/source'
```

No se deshabilita la SCC ni se fuerza un UID fijo; la corrección mantiene la
compatibilidad con `restricted-v2`.
