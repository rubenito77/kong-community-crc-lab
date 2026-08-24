# Resultado P01-01: plugin `rate-limiting`

## Resumen

| Campo | Resultado |
|---|---|
| Fecha | 2026-08-24 |
| Cluster | OpenShift Local CRC 4.22.1 |
| Kong Gateway | Community 3.9.3 |
| Kong Ingress Controller | 3.5 |
| Modo | DB-less |
| Namespace | `kong-demo` |
| Pipeline | `kong-plugin-rate-limiting` |
| PipelineRun aprobado | `kong-plugin-rate-limiting-nnpv2` |
| Resultado | **APROBADO** |

La prueba confirmó cinco solicitudes HTTP 200 dentro de la cuota, dos respuestas
HTTP 429 al excederla y HTTP 200 en `/demo2`, ruta de control no asociada al
plugin.

## Configuración validada

```yaml
plugin: rate-limiting
config:
  minute: 5
  policy: local
  limit_by: ip
  fault_tolerant: true
  hide_client_headers: false
```

El recurso `KongPlugin/demo-rate-limit` se asoció únicamente a
`Ingress/kong-echo` mediante:

```text
konghq.com/plugins=demo-rate-limit
```

`Ingress/kong-echo-2` no fue modificado.

## Ejecuciones realizadas

### Intento 1: fallo de propiedad del workspace

PipelineRun:

```text
kong-plugin-rate-limiting-tdmkj
```

Resultado:

```text
clone-repository: StepFailed
fatal: detected dubious ownership in repository at '/workspace/source'
```

Causa: OpenShift ejecutó el step con un UID dinámico mediante la SCC
`restricted-v2`, y Git rechazó el workspace por diferencia de propietario.

Corrección:

- `HOME=/tekton/home`;
- `/workspace/source` registrado como `safe.directory`;
- sin UID fijo, privilegios ni cambios de SCC.

### Intento 2: workspace no compartido

PipelineRun:

```text
kong-plugin-rate-limiting-lkds2
```

Resultados parciales:

```text
clone-repository: Succeeded
validate-baseline: Succeeded
baseline /demo: HTTP 200
baseline /demo2: HTTP 200
apply-plugin: StepFailed
```

Error:

```text
the path "/workspace/source/manifests/plugins/rate-limiting/kongplugin.yaml" does not exist
```

Causa: `emptyDir` creó un volumen independiente para cada pod/TaskRun. El pod
de aplicación no podía ver el checkout del pod de clonación.

Corrección: `volumeClaimTemplate` con PVC `ReadWriteOnce` compartido entre las
Tasks.

### Intento 3: aprobado

PipelineRun:

```text
kong-plugin-rate-limiting-nnpv2
```

Todas las Tasks finalizaron correctamente:

| Task | Resultado |
|---|---|
| `clone-repository` | `Succeeded` |
| `validate-baseline` | `Succeeded` |
| `apply-plugin` | `Succeeded` |
| `test-rate-limiting` | `Succeeded` |

Estado final del PipelineRun:

```text
SUCCEEDED=True
REASON=Completed
```

## Evidencia HTTP automatizada

```text
request=1 status=200
X-RateLimit-Remaining-Minute: 4
X-RateLimit-Limit-Minute: 5
request=2 status=200
X-RateLimit-Remaining-Minute: 3
request=3 status=200
X-RateLimit-Remaining-Minute: 2
request=4 status=200
X-RateLimit-Remaining-Minute: 1
request=5 status=200
X-RateLimit-Remaining-Minute: 0
request=6 status=429
X-RateLimit-Remaining-Minute: 0
request=7 status=429
X-RateLimit-Remaining-Minute: 0
control=/demo2 status=200
PASS: rate-limiting produjo HTTP 200 y HTTP 429; /demo2 continuo en HTTP 200
```

## Verificación externa

La Route pública también respondió correctamente:

```text
HTTP/1.1 200 OK
x-ratelimit-remaining-minute: 4
x-ratelimit-limit-minute: 5
ratelimit-remaining: 4
ratelimit-limit: 5
server: kong/3.9.3
```

El backend devolvió:

```text
Respuesta recibida a traves de Kong Community
```

## Reconciliación

La búsqueda de `error|failed|invalid|rejected` en los logs del Kong Ingress
Controller durante los diez minutos posteriores a la prueba no devolvió
resultados.

## PVC del workspace

| Campo | Valor |
|---|---|
| PVC | `pvc-4febaec25a` |
| Solicitud | `100Mi` |
| Capacidad informada | `99Gi` |
| Estado | `Bound` |
| Access mode | `RWO` |
| StorageClass | `crc-csi-hostpath-provisioner` |

La capacidad informada es un comportamiento del provisionador hostpath de CRC;
la solicitud declarada por el PipelineRun continúa siendo `100Mi`.

## Observación no bloqueante

Los steps que no definían `HOME` mostraron:

```text
warning: unsuccessful cred copy: ".docker" from "/tekton/creds" to "/":
unable to create destination directory: mkdir /.docker: permission denied
```

La advertencia no afectó el resultado. La Pipeline se ajustó para usar
`HOME=/tekton/home` en todos los steps y evitarla en ejecuciones futuras.

## Rollback

```powershell
oc annotate ingress kong-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-rate-limit -n kong-demo
```

Validación posterior:

```powershell
curl.exe -k -i https://kong-proxy-kong.apps-crc.testing/demo
curl.exe -k -i https://kong-proxy-kong.apps-crc.testing/demo2
```

Ambas rutas deben responder HTTP 200 y `/demo` ya no debe incluir headers
`X-RateLimit-*`.
