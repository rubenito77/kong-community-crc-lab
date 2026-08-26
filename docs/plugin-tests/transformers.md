# Pruebas P02-02 y P02-03: transformadores

## Objetivo

Validar `request-transformer` y `response-transformer` de manera secuencial y
observable. Se agrega la aplicación `kong-transform-echo`, que devuelve como
JSON los headers que recibe, porque las aplicaciones `hashicorp/http-echo`
existentes responden texto fijo.

## Nueva ruta de laboratorio

```text
/transform -> Ingress kong-transform-echo
           -> Service kong-transform-echo:8080
           -> Pod mendhak/http-https-echo:41
```

La imagen usa un tag fijo, ejecuta sin root y escucha HTTP en `8080`.

## Configuraciones

Request:

```yaml
plugin: request-transformer
config:
  add:
    headers:
      - X-Lab-Request-Transform:added-by-kong
```

Response:

```yaml
plugin: response-transformer
config:
  add:
    headers:
      - X-Lab-Response-Transform:added-by-kong
```

## Secuencia automatizada

| Etapa | Resultado esperado |
|---|---|
| Línea base | `/transform` responde 200 sin headers del laboratorio. |
| Request | El JSON del backend contiene `X-Lab-Request-Transform=added-by-kong`. |
| Response | El cliente recibe `X-Lab-Response-Transform: added-by-kong`. |
| Control | `/demo` y `/demo2` responden 200 sin el header de response. |

## Archivos

```text
manifests/apps/kong-transform-echo/
manifests/plugins/transformers/
pipelines/pipelines/kong-plugin-transformers.yaml
pipelines/runs/transformers-run.yaml
```

## Rollback de plugins

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-request-transformer demo-response-transformer -n kong-demo
```

## Detalle de validación, instalación y rollback

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-transformers.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-transformers.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\transformers-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

- El primer comando valida la Pipeline en el API Server sin guardarla.
- El segundo instala o actualiza la definición reutilizable.
- El tercero crea una ejecución independiente y captura el nombre generado.
- `-w` mantiene la observación hasta que el usuario la interrumpe o finaliza.
- `validate-baseline` demuestra que `/transform` responde 200 sin los headers.
- `apply-request-transformer` crea el primer CR y lo asocia al Ingress.
- `test-request-transformer` busca el header dentro del JSON del upstream: así
  se prueba que la modificación ocurrió antes de reenviar la solicitud.
- Después se agrega `demo-response-transformer` sin quitar el plugin anterior.
- `test-response-transformer` verifica el header visto por el cliente y que las
  rutas `/demo` y `/demo2` no lo reciben.

```powershell
oc get kongplugin demo-request-transformer demo-response-transformer -n kong-demo -o yaml
oc get ingress kong-transform-echo -n kong-demo -o jsonpath='{.metadata.annotations.konghq\.com/plugins}'
```

El rollback primero quita la referencia del Ingress y después elimina ambos
CR. Se conserva `kong-transform-echo`, porque es el backend observable de las
pruebas siguientes. Deben desaparecer ambos headers y `/transform` seguir en
HTTP 200.

La aplicación de observación puede conservarse para futuras pruebas de headers,
autenticación y CORS.

## Resultado real

P02-02 y P02-03 fueron aprobadas el 2026-08-25 mediante el PipelineRun
`kong-plugin-transformers-fxkqz`. La evidencia completa se encuentra en
[Resultado de transformadores](../plugin-test-results/transformers-2026-08-25.md).

## Fuentes oficiales

- [Request Transformer](https://developer.konghq.com/plugins/request-transformer/examples/add-header/)
- [Response Transformer](https://developer.konghq.com/plugins/response-transformer/examples/add-header/)
- [HTTP/HTTPS Echo](https://github.com/mendhak/docker-http-https-echo)
