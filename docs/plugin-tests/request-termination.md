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

## Fuente oficial

- [Request Termination](https://developer.konghq.com/plugins/request-termination/)
