# Resultado P01-03: Request Termination

## Resumen

| Campo | Resultado |
|---|---|
| Fecha | 2026-08-26 |
| Cluster | OpenShift Local CRC 4.22.1 |
| Kong Gateway | Community 3.9.3 |
| Kong Ingress Controller | 3.5 |
| Modo | DB-less |
| Namespace | `kong-demo` |
| Pipeline | `kong-plugin-request-termination` |
| PipelineRun | `kong-plugin-request-termination-4zht8` |
| P01-03 | **APROBADA** |

## Objetivo

Comprobar que Kong pueda deshabilitar temporalmente `/transform` con una
respuesta controlada, sin alcanzar el upstream y sin afectar `/demo` ni
`/demo2`.

## Configuración validada

```yaml
plugin: request-termination
config:
  status_code: 503
  message: Ruta temporalmente deshabilitada por Kong Community
```

El `KongPlugin/demo-request-termination` se asoció únicamente al Ingress
`kong-transform-echo`.

## Archivos involucrados

| Archivo | Estado anterior | Cambio | Estado final |
|---|---|---|---|
| `manifests/plugins/request-termination/kongplugin.yaml` | No existía. | Se definió HTTP 503 y mensaje controlado. | Manifiesto reproducible del plugin. |
| `manifests/plugins/request-termination/kustomization.yaml` | No existía. | Se agrupó el manifiesto. | Aplicable mediante Kustomize. |
| `pipelines/pipelines/kong-plugin-request-termination.yaml` | No existía. | Se agregaron línea base, aplicación y pruebas. | Pipeline aprobada. |
| `pipelines/runs/request-termination-run.yaml` | No existía. | Se agregó PipelineRun con PVC. | Evidencia conservada con `cleanup=false`. |
| `pipelines/kustomization.yaml` | No incluía P01-03. | Se registró la Pipeline. | Incluida en el laboratorio. |
| `docs/plugin-tests/request-termination.md` | No existía. | Se documentaron ejecución y rollback. | Guía PowerShell/Linux disponible. |
| `Ingress/kong-transform-echo` | `plugins` vacío; `strip-path=true`. | Se añadió `demo-request-termination`. | Terminación limitada a `/transform`. |
| `/demo` y `/demo2` | HTTP 200. | Sin cambios. | HTTP 200. |

## Comparación antes y después

| Momento | `/transform` | Evidencia |
|---|---:|---|
| Antes del plugin | HTTP 200 | JSON del backend y `X-Kong-Upstream-Latency`. |
| Después del plugin | HTTP 503 | Mensaje de Kong y sin latencia de upstream. |

La ausencia de `X-Kong-Upstream-Latency` y del JSON que devuelve
`kong-transform-echo` demuestra que la solicitud fue terminada antes de llegar
al backend.

## Resultado del PipelineRun

```text
NAME                                    SUCCEEDED   REASON
kong-plugin-request-termination-4zht8   True        Completed
```

| Task | Resultado |
|---|---|
| `clone-repository` | `Succeeded` |
| `validate-baseline` | `Succeeded` |
| `apply-plugin` | `Succeeded` |
| `test-termination` | `Succeeded` |

Evidencia de línea base:

```text
baseline /transform: HTTP 200
```

Evidencia posterior:

```text
terminated /transform status=503
control=/demo status=200
control=/demo2 status=200
PASS: /transform terminado por Kong y rutas de control aisladas
```

## Respuesta externa

```text
HTTP/1.1 503 Service Temporarily Unavailable
x-kong-response-latency: 0
server: kong/3.9.3
x-kong-request-id: 61fff83c97c6b33269e4335b4b2dc318
```

```json
{"message":"Ruta temporalmente deshabilitada por Kong Community"}
```

No se recibió `X-Kong-Upstream-Latency`.

## Estado de Kubernetes

```text
KongPlugin: demo-request-termination
plugin: request-termination
status_code: 503
Ingress plugins: demo-request-termination
Ingress strip-path: true
```

## PVC

| Campo | Valor |
|---|---|
| PVC | `pvc-2cb712a132` |
| Solicitud | 100Mi |
| Capacidad informada | 99Gi |
| Estado | Bound |
| StorageClass | `crc-csi-hostpath-provisioner` |

## Reconciliación

La búsqueda de `error|failed|invalid|rejected` en los logs recientes del Kong
Ingress Controller no devolvió resultados.

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-request-termination -n kong-demo
```

Después del rollback, `/transform` debe volver de HTTP 503 a HTTP 200.

## Conclusión

P01-03 queda aprobada para Kong Community 3.9.3 en modo DB-less. Kong terminó
la solicitud sin invocar el backend y el alcance permaneció limitado a la ruta
seleccionada.
