# Resultado P02-01: plugin `correlation-id`

## Resumen

| Campo | Resultado |
|---|---|
| Fecha | 2026-08-25 |
| Cluster | OpenShift Local CRC 4.22.1 |
| Kong Gateway | Community 3.9.3 |
| Kong Ingress Controller | 3.5 |
| Modo | DB-less |
| Namespace | `kong-demo` |
| Pipeline | `kong-plugin-correlation-id` |
| PipelineRun | `kong-plugin-correlation-id-ts78l` |
| Resultado | **APROBADO** |

La prueba confirmó que Kong genera un UUID, preserva un identificador enviado
por el cliente y mantiene `/demo2` fuera del alcance del plugin.

## Configuración validada

```yaml
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: demo-correlation-id
  namespace: kong-demo
plugin: correlation-id
config:
  header_name: X-Lab-Correlation-ID
  generator: uuid
  echo_downstream: true
```

Se utilizó `X-Lab-Correlation-ID` para distinguir claramente el header del
plugin del header nativo `X-Kong-Request-ID` de Kong.

## Archivos involucrados

| Archivo | Estado anterior | Cambio | Estado final |
|---|---|---|---|
| `manifests/plugins/correlation-id/kongplugin.yaml` | No existía. | Se agregó la configuración declarativa. | Define UUID y retorno del header al cliente. |
| `manifests/plugins/correlation-id/kustomization.yaml` | No existía. | Se agregó el recurso del plugin. | Permite aplicar el manifiesto con Kustomize. |
| `pipelines/pipelines/kong-plugin-correlation-id.yaml` | No existía. | Se creó la orquestación completa. | Ejecuta línea base, aplicación, tres casos de prueba y rollback opcional. |
| `pipelines/runs/correlation-id-run.yaml` | No existía. | Se agregó un PipelineRun con PVC compartido. | Usa `main`, RBAC dedicado, PVC `100Mi` y `cleanup=false`. |
| `pipelines/kustomization.yaml` | Incluía únicamente la Pipeline de `rate-limiting`. | Se agregó `kong-plugin-correlation-id.yaml`. | Ambas Pipelines quedan declaradas en Git. |
| `pipelines/rbac/*` | Ya existía por la prueba anterior. | No requirió cambios. | Se reutiliza `ServiceAccount/kong-plugin-tester` con permisos limitados. |
| `manifests/apps/kong-echo/ingress.yaml` | Solo contenía `strip-path`. | **No se modificó en Git.** | El recurso vivo fue anotado temporalmente por la Pipeline. |
| Deployments y Services | Operativos. | Sin cambios. | Continúan operativos con las mismas imágenes, puertos y selectores. |

## Estado del clúster antes y después

### Antes

```text
KongPlugin/demo-correlation-id: NotFound
Ingress/kong-echo plugins: vacío
/demo: HTTP 200 sin X-Lab-Correlation-ID
/demo2: HTTP 200 sin X-Lab-Correlation-ID
```

Anotaciones del Ingress:

```yaml
annotations:
  konghq.com/strip-path: "true"
```

### Después

```text
KongPlugin/demo-correlation-id: creado
Ingress/kong-echo plugins: demo-correlation-id
/demo: HTTP 200 con X-Lab-Correlation-ID
/demo2: HTTP 200 sin X-Lab-Correlation-ID
```

Anotaciones del recurso vivo:

```yaml
annotations:
  konghq.com/strip-path: "true"
  konghq.com/plugins: demo-correlation-id
```

La Pipeline realizó la asociación con:

```powershell
oc annotate ingress kong-echo `
  -n kong-demo `
  konghq.com/plugins=demo-correlation-id `
  --overwrite
```

## Resultado del PipelineRun

```text
NAME                               SUCCEEDED   REASON
kong-plugin-correlation-id-ts78l   True        Completed
```

Todas las Tasks fueron aprobadas:

| Task | Resultado |
|---|---|
| `clone-repository` | `Succeeded` |
| `validate-baseline` | `Succeeded` |
| `apply-plugin` | `Succeeded` |
| `test-correlation-id` | `Succeeded` |

No fueron necesarias correcciones ni ejecuciones adicionales.

## Evidencia automatizada

### UUID generado

```text
generated status=200 id=2ffe2710-0b8d-4adc-a9ae-ef54c3ed9c87
```

El valor cumple el formato UUID configurado.

### ID proporcionado por el cliente

```text
custom status=200
sent=lab-client-20260825
returned=lab-client-20260825
```

Kong preservó el valor sin reemplazarlo.

### Ruta de control

```text
control=/demo2 status=200
PASS: UUID generado, ID del cliente preservado y /demo2 sin correlation-id
```

## Evidencia externa

### Generación

```text
HTTP/1.1 200 OK
x-lab-correlation-id: 0e1c9200-c151-417a-8d3a-dc71c4074850
x-kong-request-id: f48ed12e03281c1fb54ecf3151677b68
```

Esto confirma que el header del plugin y el identificador nativo de Kong son
independientes.

### Propagación

Solicitud:

```powershell
curl.exe -k -sS -D - -o NUL `
  -H "X-Lab-Correlation-ID: prueba-cliente-powershell" `
  https://kong-proxy-kong.apps-crc.testing/demo
```

Respuesta:

```text
HTTP/1.1 200 OK
x-lab-correlation-id: prueba-cliente-powershell
```

### Aislamiento

```text
GET /demo2
HTTP/1.1 200 OK
X-Lab-Correlation-ID: ausente
```

## Flujo antes y después

Antes:

```text
/demo  -> Ingress -> Service kong-echo -> Pod
/demo2 -> Ingress -> Service kong-echo-2 -> Pod
```

Después:

```text
/demo  -> correlation-id -> Ingress -> Service kong-echo -> Pod
/demo2 -> Ingress -> Service kong-echo-2 -> Pod
```

## Reconciliación

La búsqueda de `error|failed|invalid|rejected` en los logs del Kong Ingress
Controller durante los diez minutos posteriores no devolvió resultados.

## Rollback

```powershell
oc annotate ingress kong-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-correlation-id -n kong-demo
```

Después del rollback, `/demo` y `/demo2` deben responder HTTP 200 y ninguna ruta
debe incluir `X-Lab-Correlation-ID`.

## Fuente oficial

- [Kong Correlation ID plugin](https://developer.konghq.com/plugins/correlation-id/)
