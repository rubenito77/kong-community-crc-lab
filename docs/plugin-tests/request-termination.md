# Prueba P01-03: Request Termination

## Objetivo

Validar que Kong pueda deshabilitar temporalmente `/transform` con HTTP 503 y
un mensaje controlado, sin invocar el backend ni afectar `/demo` y `/demo2`.

## Configuración

```yaml
plugin: request-termination
config:
  status_code: 503
  message: Ruta temporalmente deshabilitada por Kong Community
```

| Etapa | `/transform` | `/demo` | `/demo2` |
|---|---:|---:|---:|
| Línea base | 200 | 200 | 200 |
| Plugin aplicado | 503 | 200 | 200 |
| Rollback | 200 | 200 | 200 |

La ausencia del JSON del backend y de `X-Kong-Upstream-Latency` en la respuesta
503 demuestra que Kong terminó la solicitud antes de alcanzar el upstream.

## PowerShell

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-request-termination.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-request-termination.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\request-termination-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

## Linux

```bash
oc apply -f pipelines/pipelines/kong-plugin-request-termination.yaml --dry-run=server
oc apply -f pipelines/pipelines/kong-plugin-request-termination.yaml
PIPELINE_RUN="$(oc create -f pipelines/runs/request-termination-run.yaml -o jsonpath='{.metadata.name}')"
oc get pipelinerun "$PIPELINE_RUN" -n kong-demo -w
```

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-request-termination -n kong-demo
```

## Detalle de cada comando y validación

- `oc apply ... --dry-run=server`: valida la Pipeline sin modificar el cluster.
- `oc apply -f ...`: crea o actualiza la Pipeline.
- `oc create -f pipelines/runs/request-termination-run.yaml`: inicia una
  ejecución nueva; no reutiliza un PipelineRun anterior.
- `validate-baseline`: confirma que Kong alcanza el upstream y obtiene 200.
- `apply-plugin`: crea el CR y anota el Ingress; KIC traduce ambos recursos a la
  configuración DB-less de Kong.
- `test-termination`: exige 503 y el mensaje configurado, verifica que no exista
  respuesta del backend y mantiene `/demo` y `/demo2` en 200.

```powershell
oc get kongplugin demo-request-termination -n kong-demo -o yaml
curl.exe -k -sS -D - https://kong-proxy-kong.apps-crc.testing/transform
```

El primer comando muestra la configuración efectiva. El segundo permite ver
`server: kong`, `x-kong-response-latency` y la ausencia de
`x-kong-upstream-latency`, evidencia de que la respuesta terminó en Kong.

En el rollback primero se elimina la asociación y luego el CR. Al repetir el
curl debe regresar HTTP 200, JSON del backend y `x-kong-upstream-latency`.

## Resultado real

P01-03 fue aprobada el 2026-08-26 mediante el PipelineRun
`kong-plugin-request-termination-4zht8`. La evidencia completa se encuentra en
[Resultado de Request Termination](../plugin-test-results/request-termination-2026-08-26.md).

## Fuente oficial

- [Request Termination](https://developer.konghq.com/plugins/request-termination/)
