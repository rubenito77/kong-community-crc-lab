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

## Detalle de cada comando y validación

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-request-size-limiting.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-request-size-limiting.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\request-size-limiting-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

El `dry-run` valida sin escribir. `apply` hace converger la Pipeline declarada.
`create` inicia una corrida nueva y `jsonpath` devuelve únicamente su nombre.
La Pipeline crea payloads exactos: primero prueba 2048 bytes sin plugin (200),
aplica el límite de 1 KiB y después prueba 512 bytes (200) y 2048 bytes (413).
Finalmente consulta `/demo` y `/demo2` para verificar aislamiento.

```powershell
$TEST_POD = oc get pod -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN,tekton.dev/pipelineTask=test-request-size" -o jsonpath='{.items[0].metadata.name}'
oc logs $TEST_POD -n kong-demo -c step-execute
oc get kongplugin demo-request-size-limit -n kong-demo -o yaml
```

Estos comandos seleccionan el pod exacto, muestran los tamaños/códigos medidos
y permiten confirmar `allowed_payload_size: 1` y `size_unit: kilobytes`.
El rollback desasocia antes de borrar para evitar una referencia inválida. Se
repite el POST de 2048 bytes: debe volver a HTTP 200.

## Resultado real

P01-02 fue aprobada el 2026-08-26 mediante el PipelineRun
`kong-plugin-request-size-limiting-fzffl`. La evidencia completa se encuentra
en [Resultado de Request Size Limiting](../plugin-test-results/request-size-limiting-2026-08-26.md).

## Fuente oficial

- [Request Size Limiting](https://developer.konghq.com/plugins/request-size-limiting/reference/)
