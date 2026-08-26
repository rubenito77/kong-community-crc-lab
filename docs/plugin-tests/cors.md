# Pruebas P02-04 y P02-05: CORS

## Objetivo

Validar el plugin Community `cors` sobre `/transform`: preflight y GET desde un
origen autorizado, ausencia de permisos para un origen no autorizado y
aislamiento de `/demo` y `/demo2`.

## Alcance

El `KongPlugin` se asocia únicamente al Ingress `kong-transform-echo`. La ruta
es path-based (`/transform`), por lo que evita la limitación de los preflight
que no pueden asociarse a rutas configuradas solamente por `Host`.

## Configuración

| Campo | Valor |
|---|---|
| Origen permitido | `https://cliente-lab.example` |
| Métodos | `GET`, `OPTIONS` |
| Headers permitidos | `Accept`, `Content-Type`, `X-Lab-Client` |
| Header expuesto | `X-Lab-CORS` |
| Credenciales | `false` |
| Cache de preflight | `600` segundos |
| Continuar preflight al upstream | `false` |

## Secuencia automatizada

| Etapa | Resultado esperado |
|---|---|
| Línea base | `/transform` responde 200 sin `Access-Control-Allow-Origin`. |
| Preflight permitido | `OPTIONS` responde 200 o 204 y declara origen, método, header y max-age. |
| GET permitido | Responde 200 con el origen autorizado en `Access-Control-Allow-Origin`. |
| Origen no autorizado | No refleja el origen enviado ni devuelve `*`; mantiene el origen permitido, por lo que el navegador bloquea el acceso. |
| Controles | `/demo` y `/demo2` continúan en 200 sin headers CORS. |

## Archivos

```text
manifests/plugins/cors/kongplugin.yaml
manifests/plugins/cors/kustomization.yaml
pipelines/pipelines/kong-plugin-cors.yaml
pipelines/runs/cors-run.yaml
docs/plugin-tests/cors.md
```

## Ejecución en PowerShell

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-cors.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-cors.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\cors-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

## Ejecución en Linux

```bash
oc apply -f pipelines/pipelines/kong-plugin-cors.yaml --dry-run=server
oc apply -f pipelines/pipelines/kong-plugin-cors.yaml
PIPELINE_RUN="$(oc create -f pipelines/runs/cors-run.yaml -o jsonpath='{.metadata.name}')"
oc get pipelinerun "$PIPELINE_RUN" -n kong-demo -w
```

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-cors -n kong-demo
```

## Detalle de cada operación

- `oc apply ... --dry-run=server` valida la Pipeline sin persistirla.
- `oc apply -f ...` instala o actualiza `Pipeline/kong-plugin-cors`.
- `oc create -f ... -o jsonpath=...` genera un PipelineRun nuevo y guarda su
  nombre en `$PIPELINE_RUN`.
- `validate-baseline` comprueba HTTP 200 sin headers `Access-Control-*`.
- `apply-plugin` crea `KongPlugin/demo-cors` y lo asocia solamente a
  `Ingress/kong-transform-echo`.
- `test-cors` ejecuta `OPTIONS` con `Origin`, método y headers solicitados;
  valida las cabeceras de autorización y luego ejecuta GET permitido, GET con
  origen no autorizado y las rutas de control.

```powershell
oc get taskrun,pod -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN"
$TEST_POD = oc get pod -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN,tekton.dev/pipelineTask=test-cors" -o jsonpath='{.items[0].metadata.name}'
oc logs $TEST_POD -n kong-demo -c step-execute
```

El primer comando muestra cada tarea y pod. El selector compuesto obtiene solo
el pod de prueba CORS y `oc logs ... -c step-execute` muestra sus aserciones.

Durante el rollback, el `-` final en `konghq.com/plugins-` significa “eliminar
esta anotación”. El segundo comando borra el CR. La comprobación final exige
`/transform` en 200 sin headers CORS y ambas rutas de control en 200.

La aplicación `kong-transform-echo` se conserva para pruebas posteriores.

## Resultado real

P02-04 y P02-05 fueron aprobadas el 2026-08-25 mediante el PipelineRun
`kong-plugin-cors-2r66w`. La evidencia completa se encuentra en
[Resultado de CORS](../plugin-test-results/cors-2026-08-25.md).

## Fuentes oficiales

- [CORS plugin](https://developer.konghq.com/plugins/cors/)
- [CORS configuration reference](https://developer.konghq.com/plugins/cors/reference/)
- [KIC plugin annotation](https://developer.konghq.com/kubernetes-ingress-controller/reference/annotations/)
