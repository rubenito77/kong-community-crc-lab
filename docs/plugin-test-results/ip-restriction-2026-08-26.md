# Resultado P01-04: IP Restriction

## Resumen

| Campo | Resultado |
|---|---|
| Fecha | 2026-08-26 |
| Cluster | OpenShift Local CRC 4.22.1 |
| Kong Gateway | Community 3.9.3 |
| Kong Ingress Controller | 3.5 |
| Modo | DB-less |
| Namespace | `kong-demo` |
| Pipeline | `kong-plugin-ip-restriction` |
| PipelineRun | `kong-plugin-ip-restriction-8cvm2` |
| P01-04 | **APROBADA** |

## Descubrimiento de la IP efectiva

El backend observable recibió:

```text
x-forwarded-for: 192.168.127.1, 10.217.0.2
x-real-ip: 10.217.0.2
forwarded: for=192.168.127.1;host=kong-proxy-kong.apps-crc.testing;proto=https
ip: 192.168.127.1
```

Sin embargo, el access log de Kong registró:

```text
10.217.0.2 ... "GET /transform HTTP/1.1" 200
```

No estaban definidas `KONG_TRUSTED_IPS`, `KONG_REAL_IP_HEADER` ni
`KONG_REAL_IP_RECURSIVE`. Un Pod Tekton usando la Route pública también llegó a
Kong como `10.217.0.2`. Por ello, el CIDR probado fue `10.217.0.2/32`.

## Configuraciones validadas

Denegación:

```yaml
plugin: ip-restriction
config:
  deny:
    - 10.217.0.2/32
```

Permiso:

```yaml
plugin: ip-restriction
config:
  allow:
    - 10.217.0.2/32
```

Se usaron dos recursos separados, `demo-ip-deny` y `demo-ip-allow`, para que
cada configuración fuera explícita y no conservara campos de la fase anterior.

## Archivos involucrados

| Archivo | Estado anterior | Cambio | Estado final |
|---|---|---|---|
| `manifests/plugins/ip-restriction/deny.yaml` | No existía. | Se añadió la regla deny. | Recurso `demo-ip-deny`. |
| `manifests/plugins/ip-restriction/allow.yaml` | No existía. | Se añadió la regla allow. | Recurso `demo-ip-allow`. |
| `manifests/plugins/ip-restriction/kustomization.yaml` | No existía. | Agrupa ambas reglas. | Aplicable mediante Kustomize. |
| `pipelines/pipelines/kong-plugin-ip-restriction.yaml` | No existía. | Automatiza línea base, deny y allow. | Pipeline aprobada. |
| `pipelines/runs/ip-restriction-run.yaml` | No existía. | Usa Route pública y PVC. | Evidencia conservada. |
| `pipelines/kustomization.yaml` | No incluía P01-04. | Registra la Pipeline. | Incluida en el laboratorio. |
| `docs/plugin-tests/ip-restriction.md` | No existía. | Documenta descubrimiento y ejecución. | Guía PowerShell/Linux. |
| `Ingress/kong-transform-echo` | Sin plugins. | `demo-ip-deny` y luego `demo-ip-allow`. | Estado final: allow asociado. |

## Comparación

| Etapa | Configuración | `/transform` | Upstream |
|---|---|---:|---|
| Línea base | Sin plugin | 200 | Alcanzado |
| Denegación | `deny: 10.217.0.2/32` | 403 | No alcanzado |
| Permiso | `allow: 10.217.0.2/32` | 200 | Alcanzado |

## Resultado del PipelineRun

Las seis Tasks finalizaron en `Succeeded`:

```text
clone-repository
validate-baseline
apply-deny
test-deny
apply-allow
test-allow
```

Evidencia:

```text
baseline /transform: HTTP 200
deny cidr=10.217.0.2/32 status=403
control=/demo status=200
control=/demo2 status=200
allow cidr=10.217.0.2/32 status=200
PASS: IP denegada y permitida; rutas de control aisladas
```

## Estado final externo

```text
HTTP/1.1 200 OK
server: kong/3.9.3
x-kong-upstream-latency: 2
x-kong-proxy-latency: 1
```

La presencia de `X-Kong-Upstream-Latency` confirma que la fase allow permitió
alcanzar `kong-transform-echo`.

## PVC

| Campo | Valor |
|---|---|
| PVC | `pvc-e737d3a947` |
| Solicitud | 100Mi |
| Capacidad informada | 99Gi |
| Estado | Bound |
| StorageClass | `crc-csi-hostpath-provisioner` |

## Reconciliación

La búsqueda de `error|failed|invalid|rejected` en los logs recientes de KIC no
devolvió resultados.

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-ip-deny demo-ip-allow -n kong-demo
```

Después del rollback, `/transform`, `/demo` y `/demo2` deben responder 200.

## Consideración para otros clusters

`10.217.0.2` es específico de este CRC y de su recorrido de red. En otro
cluster se debe repetir el descubrimiento antes de configurar allow/deny. Si se
requiere filtrar por la IP original del usuario, primero debe diseñarse y
validarse la configuración de trusted IP y real IP de Kong.

## Conclusión

P01-04 queda aprobada para este laboratorio. Kong bloqueó y permitió el CIDR
efectivo de forma granular sin afectar otras rutas.
