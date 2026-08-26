# Prueba P01-04: IP Restriction

## Descubrimiento de la IP efectiva

El backend recibió `X-Forwarded-For: 192.168.127.1, 10.217.0.2`, pero Kong
registró la conexión como `10.217.0.2`. No existen variables explícitas
`KONG_TRUSTED_IPS`, `KONG_REAL_IP_HEADER` ni `KONG_REAL_IP_RECURSIVE`.

Un Pod Tekton atravesando la Route pública también fue registrado como
`10.217.0.2`, por lo que la prueba usa `10.217.0.2/32`.

## Casos

| Etapa | Configuración | `/transform` |
|---|---|---:|
| Línea base | Sin plugin | 200 |
| Denegación | `deny: 10.217.0.2/32` | 403 |
| Permiso | `allow: 10.217.0.2/32` | 200 |

`/demo` y `/demo2` permanecen en HTTP 200. La Pipeline usa la Route pública,
no el Service interno, para conservar el recorrido real.

## PowerShell

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-ip-restriction.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-ip-restriction.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\ip-restriction-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

## Linux

```bash
oc apply -f pipelines/pipelines/kong-plugin-ip-restriction.yaml --dry-run=server
oc apply -f pipelines/pipelines/kong-plugin-ip-restriction.yaml
PIPELINE_RUN="$(oc create -f pipelines/runs/ip-restriction-run.yaml -o jsonpath='{.metadata.name}')"
oc get pipelinerun "$PIPELINE_RUN" -n kong-demo -w
```

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-ip-deny demo-ip-allow -n kong-demo
```

## Detalle de validación, instalación y rollback

La fase de descubrimiento es obligatoria porque Kong ve la IP del router
OpenShift (`10.217.0.2`) y no directamente la IP del cliente externo.

```powershell
oc exec -n kong $KONG_POD -c proxy -- env |
  Select-String -Pattern '^KONG_(TRUSTED_IPS|REAL_IP_HEADER|REAL_IP_RECURSIVE|PROXY_LISTEN)='
oc logs deployment/kong-kong -n kong -c proxy --since=2m
```

El primer comando inspecciona la configuración de real-IP sin mostrar secretos;
el segundo confirma la IP que Kong registra para una solicitud identificada.

La Pipeline valida primero 200, aplica `demo-ip-deny`, espera reconciliación y
exige 403. Luego reemplaza la anotación por `demo-ip-allow` y exige 200. Ambas
fases consultan la Route pública para mantener el recorrido real por el router.

```powershell
oc get kongplugin demo-ip-deny demo-ip-allow -n kong-demo -o yaml
oc get ingress kong-transform-echo -n kong-demo -o jsonpath='{.metadata.annotations.konghq\.com/plugins}'
```

El primer comando demuestra los CIDR configurados; el segundo muestra cuál de
los dos plugins está activo (al finalizar debe ser `demo-ip-allow`). El rollback
quita esa asociación y elimina ambos CR, incluido el de denegación ya inactivo.
Se confirman las tres rutas en 200 y logs del controlador sin errores.

## Resultado real

P01-04 fue aprobada el 2026-08-26 mediante el PipelineRun
`kong-plugin-ip-restriction-8cvm2`. La evidencia completa se encuentra en
[Resultado de IP Restriction](../plugin-test-results/ip-restriction-2026-08-26.md).

## Fuentes oficiales

- [Deny IP range](https://developer.konghq.com/plugins/ip-restriction/examples/deny/)
- [Allow IP and range](https://developer.konghq.com/plugins/ip-restriction/examples/allow/)
