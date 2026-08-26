# Prueba P02-01: plugin `correlation-id`

## Objetivo

Validar el plugin Community `correlation-id` sobre `/demo` sin afectar
`/demo2`. La prueba usa el header `X-Lab-Correlation-ID` para distinguirlo del
header nativo `X-Kong-Request-ID`.

## Configuración

```yaml
plugin: correlation-id
config:
  header_name: X-Lab-Correlation-ID
  generator: uuid
  echo_downstream: true
```

## Casos automatizados

| Caso | Solicitud | Resultado esperado |
|---|---|---|
| Línea base | `/demo` y `/demo2` antes del plugin | HTTP 200 sin `X-Lab-Correlation-ID`. |
| Generación | `/demo` sin header | HTTP 200 y UUID generado en `X-Lab-Correlation-ID`. |
| Propagación | `/demo` con `X-Lab-Correlation-ID: lab-client-20260825` | Kong conserva y devuelve exactamente ese valor. |
| Aislamiento | `/demo2` sin header | HTTP 200 sin `X-Lab-Correlation-ID`. |

## Archivos involucrados

| Archivo | Función |
|---|---|
| `manifests/plugins/correlation-id/kongplugin.yaml` | Configuración del plugin. |
| `pipelines/pipelines/kong-plugin-correlation-id.yaml` | Orquestación y validaciones. |
| `pipelines/runs/correlation-id-run.yaml` | Ejecución con PVC compartido. |
| `pipelines/rbac/*` | Identidad y permisos reutilizados de la prueba anterior. |

## Estado antes de la prueba

```text
KongPlugin/demo-correlation-id: no existe
Ingress/kong-echo plugins: vacío
/demo: HTTP 200 sin X-Lab-Correlation-ID
/demo2: HTTP 200 sin X-Lab-Correlation-ID
```

## Estado esperado después de aplicar el plugin

```yaml
annotations:
  konghq.com/strip-path: "true"
  konghq.com/plugins: demo-correlation-id
```

No se modifican Deployment ni Service. La anotación se agrega al recurso vivo
durante la Pipeline y el manifiesto base del Ingress permanece sin plugins.

## Rollback

```powershell
oc annotate ingress kong-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-correlation-id -n kong-demo
```

## Detalle de validación, instalación y rollback

1. `oc apply ... --dry-run=server` envía la definición de la Pipeline al API
   Server para validar CRD, esquema y admisión, pero no persiste cambios.
2. `oc apply -f ...` crea o actualiza `Pipeline/kong-plugin-correlation-id`.
3. `oc create -f pipelines/runs/correlation-id-run.yaml` crea siempre un
   PipelineRun nuevo; `-o jsonpath` captura su nombre generado.
4. La tarea `validate-baseline` comprueba `/demo` y `/demo2` en 200 y confirma
   que el header del laboratorio no existe antes de activar el plugin.
5. `apply-plugin` crea `KongPlugin/demo-correlation-id` y agrega
   `konghq.com/plugins=demo-correlation-id` al Ingress `kong-echo`.
6. `test-correlation-id` comprueba un UUID generado, preservación de un ID
   enviado por el cliente y ausencia del header en `/demo2`.
7. Para inspeccionar la ejecución:

```powershell
oc get taskrun,pod -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN"
oc logs -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN" --all-containers=true --prefix=true
oc get kongplugin demo-correlation-id -n kong-demo -o yaml
```

En el rollback, `konghq.com/plugins-` elimina únicamente esa anotación. Luego
se elimina el `KongPlugin`; el Deployment, Service e Ingress permanecen. Se
confirma `/demo` y `/demo2` en 200 y sin `X-Lab-Correlation-ID`.

La evidencia real, PipelineRun, headers y cualquier corrección necesaria se
registrarán después de ejecutar la prueba en CRC.

## Resultado real

La prueba fue aprobada el 2026-08-25 mediante el PipelineRun
`kong-plugin-correlation-id-ts78l`. La evidencia completa se encuentra en
[Resultado P02-01](../plugin-test-results/correlation-id-2026-08-25.md).

## Fuente oficial

- [Kong Correlation ID plugin](https://developer.konghq.com/plugins/correlation-id/)
