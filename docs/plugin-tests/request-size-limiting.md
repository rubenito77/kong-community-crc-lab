# Prueba P01-02: Request Size Limiting

## Objetivo

Validar que Kong permita un payload dentro del límite y rechace con HTTP 413
otro payload que lo supere, sin afectar `/demo` ni `/demo2`.

## Configuración

```yaml
plugin: request-size-limiting
config:
  allowed_payload_size: 1
  size_unit: kilobytes
```

El plugin se asocia solamente al Ingress `kong-transform-echo` (`/transform`).

| Caso | Tamaño | Resultado esperado |
|---|---:|---|
| Línea base sin plugin | 2048 bytes | HTTP 200 |
| Payload permitido | 512 bytes | HTTP 200 |
| Payload excesivo | 2048 bytes | HTTP 413 |
| Controles | GET `/demo` y `/demo2` | HTTP 200 |

## Ejecución en PowerShell

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-request-size-limiting.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-request-size-limiting.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\request-size-limiting-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

## Ejecución en Linux

```bash
oc apply -f pipelines/pipelines/kong-plugin-request-size-limiting.yaml --dry-run=server
oc apply -f pipelines/pipelines/kong-plugin-request-size-limiting.yaml
PIPELINE_RUN="$(oc create -f pipelines/runs/request-size-limiting-run.yaml -o jsonpath='{.metadata.name}')"
oc get pipelinerun "$PIPELINE_RUN" -n kong-demo -w
```

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-request-size-limit -n kong-demo
```

## Fuente oficial

- [Request Size Limiting](https://developer.konghq.com/plugins/request-size-limiting/reference/)
