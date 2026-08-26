# Resultado P01-02: Request Size Limiting

## Resumen

| Campo | Resultado |
|---|---|
| Fecha | 2026-08-26 |
| Cluster | OpenShift Local CRC 4.22.1 |
| Kong Gateway | Community 3.9.3 |
| Kong Ingress Controller | 3.5 |
| Modo | DB-less |
| Namespace | `kong-demo` |
| Pipeline | `kong-plugin-request-size-limiting` |
| PipelineRun | `kong-plugin-request-size-limiting-fzffl` |
| P01-02 | **APROBADA** |

## Objetivo

Comprobar que Kong permita solicitudes dentro de un límite de 1 KiB y rechace
con HTTP 413 las que lo superen, sin afectar las rutas `/demo` y `/demo2`.

## Configuración validada

```yaml
plugin: request-size-limiting
config:
  allowed_payload_size: 1
  size_unit: kilobytes
```

El `KongPlugin/demo-request-size-limit` se asoció únicamente al Ingress
`kong-transform-echo`, que publica `/transform`.

## Archivos involucrados

| Archivo | Estado anterior | Cambio | Estado final |
|---|---|---|---|
| `manifests/plugins/request-size-limiting/kongplugin.yaml` | No existía. | Se definió un límite de 1 KiB. | Manifiesto reproducible del plugin. |
| `manifests/plugins/request-size-limiting/kustomization.yaml` | No existía. | Se agrupó el manifiesto. | Aplicable mediante Kustomize. |
| `pipelines/pipelines/kong-plugin-request-size-limiting.yaml` | No existía. | Se agregaron línea base, aplicación y pruebas. | Pipeline aprobada. |
| `pipelines/runs/request-size-limiting-run.yaml` | No existía. | Se agregó PipelineRun con PVC. | Evidencia conservada con `cleanup=false`. |
| `pipelines/kustomization.yaml` | No incluía P01-02. | Se registró la Pipeline. | Incluida en el conjunto del laboratorio. |
| `docs/plugin-tests/request-size-limiting.md` | No existía. | Se documentaron ejecución y rollback. | Guía PowerShell/Linux disponible. |
| `Ingress/kong-transform-echo` | `plugins` vacío; `strip-path=true`. | Se añadió `demo-request-size-limit`. | Límite aplicado sólo a `/transform`. |
| `/demo` y `/demo2` | HTTP 200. | Sin cambios. | HTTP 200. |

## Comparación antes y después

| Momento | Payload | Resultado |
|---|---:|---|
| Antes del plugin | 2048 bytes | HTTP 200 |
| Después del plugin | 512 bytes | HTTP 200 |
| Después del plugin | 2048 bytes | HTTP 413 |

La línea base demuestra que el backend aceptaba 2048 bytes. El cambio de 200 a
413 para el mismo tamaño fue introducido por Kong.

## Resultado del PipelineRun

```text
NAME                                      SUCCEEDED   REASON
kong-plugin-request-size-limiting-fzffl   True        Completed
```

| Task | Resultado |
|---|---|
| `clone-repository` | `Succeeded` |
| `validate-baseline` | `Succeeded` |
| `apply-plugin` | `Succeeded` |
| `test-request-size` | `Succeeded` |

Evidencia de línea base:

```text
baseline 2048 bytes: HTTP 200
```

Evidencia posterior:

```text
allowed bytes=512 status=200
rejected bytes=2048 status=413
control=/demo status=200
control=/demo2 status=200
PASS: 512 bytes permitidos, 2048 bytes rechazados y controles aislados
```

## Estado de Kubernetes

```text
KongPlugin: demo-request-size-limit
plugin: request-size-limiting
allowed_payload_size: 1
size_unit: kilobytes
Ingress plugins: demo-request-size-limit
Ingress strip-path: true
```

## PVC

| Campo | Valor |
|---|---|
| PVC | `pvc-ba3eca3449` |
| Solicitud | 100Mi |
| Capacidad informada | 99Gi |
| Estado | Bound |
| StorageClass | `crc-csi-hostpath-provisioner` |

La capacidad de 99Gi corresponde al comportamiento del provisionador hostpath
de CRC, aunque el PipelineRun solicitó 100Mi.

## Reconciliación

La búsqueda de `error|failed|invalid|rejected` en los logs recientes del Kong
Ingress Controller no devolvió resultados.

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-request-size-limit -n kong-demo
```

Después del rollback, un payload de 2048 bytes debe volver a responder HTTP 200.

## Conclusión

P01-02 queda aprobada para Kong Community 3.9.3 en modo DB-less. El plugin
rechazó correctamente el payload excesivo y permaneció aislado de las demás
rutas.
