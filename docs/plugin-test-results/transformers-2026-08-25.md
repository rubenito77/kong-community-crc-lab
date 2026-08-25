# Resultados P02-02 y P02-03: transformadores

## Resumen

| Campo | Resultado |
|---|---|
| Fecha | 2026-08-25 |
| Cluster | OpenShift Local CRC 4.22.1 |
| Kong Gateway | Community 3.9.3 |
| Kong Ingress Controller | 3.5 |
| Modo | DB-less |
| Namespace | `kong-demo` |
| Pipeline | `kong-plugin-transformers` |
| PipelineRun | `kong-plugin-transformers-fxkqz` |
| P02-02 `request-transformer` | **APROBADA** |
| P02-03 `response-transformer` | **APROBADA** |

## Aplicación de observación

Se agregó una tercera aplicación porque `hashicorp/http-echo` devuelve texto
fijo y no permite demostrar qué headers recibió el upstream.

```text
/transform -> Ingress kong-transform-echo
           -> Service kong-transform-echo:8080
           -> Pod mendhak/http-https-echo:41
```

Estado validado:

```text
Deployment: 1/1 Available
Pod: 1/1 Running
Service: ClusterIP 8080/TCP
IngressClass: kong
/transform: HTTP 200
```

La imagen usa un tag fijo, ejecuta sin root y resultó compatible con la SCC de
OpenShift.

## Archivos involucrados

| Archivo | Estado anterior | Cambio | Estado final |
|---|---|---|---|
| `manifests/apps/kong-transform-echo/deployment.yaml` | No existía. | Se agregó backend observable con imagen `mendhak/http-https-echo:41`. | Deployment `1/1` en puerto 8080. |
| `manifests/apps/kong-transform-echo/service.yaml` | No existía. | Se agregó Service ClusterIP. | Expone internamente `8080/TCP`. |
| `manifests/apps/kong-transform-echo/ingress.yaml` | No existía. | Se agregó Ingress de clase `kong`. | Publica `/transform` con `strip-path=true`. |
| `manifests/apps/kong-transform-echo/kustomization.yaml` | No existía. | Agrupa Deployment, Service e Ingress. | Despliegue reproducible con `oc apply -k`. |
| `manifests/plugins/transformers/request-transformer.yaml` | No existía. | Se agregó P02-02. | Añade header antes de enviar al upstream. |
| `manifests/plugins/transformers/response-transformer.yaml` | No existía. | Se agregó P02-03. | Añade header antes de responder al cliente. |
| `pipelines/pipelines/kong-plugin-transformers.yaml` | No existía. | Se creó secuencia de seis Tasks. | Valida ambos plugins de manera separada y secuencial. |
| `pipelines/runs/transformers-run.yaml` | No existía. | Se agregó ejecución con PVC compartido. | Usa `cleanup=false` para inspección posterior. |
| `pipelines/kustomization.yaml` | No incluía esta Pipeline. | Se agregó `kong-plugin-transformers.yaml`. | La Pipeline queda declarada junto a las anteriores. |
| `pipelines/rbac/*` | Ya existía. | Sin cambios. | Reutiliza identidad y permisos limitados. |
| Deployments y Services `/demo`, `/demo2` | Operativos. | Sin cambios. | Permanecieron en HTTP 200. |

## Configuraciones validadas

### P02-02: request

```yaml
plugin: request-transformer
config:
  add:
    headers:
      - X-Lab-Request-Transform:added-by-kong
```

### P02-03: response

```yaml
plugin: response-transformer
config:
  add:
    headers:
      - X-Lab-Response-Transform:added-by-kong
```

## Estado antes y después

### Antes

```text
KongPlugin/demo-request-transformer: NotFound
KongPlugin/demo-response-transformer: NotFound
Ingress/kong-transform-echo plugins: vacío
/transform: HTTP 200
Request header del laboratorio en JSON: ausente
Response header del laboratorio: ausente
```

```yaml
annotations:
  konghq.com/strip-path: "true"
```

### Después de P02-02

```yaml
annotations:
  konghq.com/strip-path: "true"
  konghq.com/plugins: demo-request-transformer
```

El backend recibió:

```json
{
  "headers": {
    "x-lab-request-transform": "added-by-kong"
  }
}
```

### Después de P02-03

```yaml
annotations:
  konghq.com/strip-path: "true"
  konghq.com/plugins: demo-request-transformer,demo-response-transformer
```

El cliente recibió:

```text
x-lab-response-transform: added-by-kong
```

## Resultado del PipelineRun

```text
NAME                             SUCCEEDED   REASON
kong-plugin-transformers-fxkqz   True        Completed
```

| Task | Resultado |
|---|---|
| `clone-repository` | `Succeeded` |
| `validate-baseline` | `Succeeded` |
| `apply-request-transformer` | `Succeeded` |
| `test-request-transformer` | `Succeeded` |
| `apply-response-transformer` | `Succeeded` |
| `test-response-transformer` | `Succeeded` |

## Evidencia P02-02

Automatizada:

```text
request-transformer status=200
PASS request-transformer: upstream recibio X-Lab-Request-Transform
```

Externa, obtenida del JSON real del backend:

```text
"x-lab-request-transform": "added-by-kong"
```

Esto demuestra que la transformación ocurrió antes de enviar la solicitud al
upstream; no es solamente un header de respuesta generado para el cliente.

## Evidencia P02-03

Automatizada:

```text
response-transformer status=200
control=/demo status=200
control=/demo2 status=200
PASS response-transformer: header agregado y rutas de control aisladas
```

Externa:

```text
HTTP/1.1 200 OK
x-lab-response-transform: added-by-kong
x-kong-request-id: 19b5340dfa65457d4e1c991125ffe114
```

Las rutas de control devolvieron:

```text
/demo: HTTP 200 sin X-Lab-Response-Transform
/demo2: HTTP 200 sin X-Lab-Response-Transform
```

## PVC

| Campo | Valor |
|---|---|
| PVC | `pvc-ba7d1d1608` |
| Solicitud | `100Mi` |
| Capacidad informada | `99Gi` |
| Estado | `Bound` |
| StorageClass | `crc-csi-hostpath-provisioner` |

## Reconciliación

La búsqueda de `error|failed|invalid|rejected` en los logs de KIC durante los
diez minutos posteriores no devolvió resultados.

## Flujo antes y después

Antes:

```text
/transform -> Kong -> backend observable
```

Después:

```text
Cliente
  -> request-transformer agrega header de request
  -> backend observable recibe el header
  -> response-transformer agrega header de response
  -> cliente recibe el header
```

`/demo` y `/demo2` no atraviesan estos plugins.

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-request-transformer demo-response-transformer -n kong-demo
```

La aplicación `kong-transform-echo` se conserva para futuras pruebas de CORS,
headers, autenticación y observabilidad.

## Fuentes oficiales

- [Request Transformer](https://developer.konghq.com/plugins/request-transformer/examples/add-header/)
- [Response Transformer](https://developer.konghq.com/plugins/response-transformer/examples/add-header/)
- [HTTP/HTTPS Echo](https://github.com/mendhak/docker-http-https-echo)
