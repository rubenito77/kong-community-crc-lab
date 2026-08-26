# Resultado P03-02: Basic Authentication

## Resumen

| Campo | Resultado |
|---|---|
| Fecha | 2026-08-26 |
| Cluster | OpenShift Local CRC 4.22.1 |
| Kong Gateway | Community 3.9.3 |
| Kong Ingress Controller | 3.5 |
| Modo | DB-less |
| Namespace | `kong-demo` |
| Pipeline | `kong-plugin-basic-auth` |
| PipelineRun | `kong-plugin-basic-auth-rxq7f` |
| P03-02 | **APROBADA** |

## Seguridad de la credencial

El PipelineRun generó la contraseña dentro del Pod Tekton. No se almacenó en
Git, parámetros, PVC, logs ni evidencia. Un `emptyDir` la compartió entre los
Steps `configure` y `test`; el archivo efímero fue eliminado al terminar.

El Secret se verificó únicamente mediante metadatos:

```text
NAME                         TYPE     CREDENTIAL_TYPE
demo-basic-auth-credential   Opaque   basic-auth
```

No se registró `.data.username` ni `.data.password`, porque sus valores Base64
son reversibles.

## Recursos configurados

```text
KongPlugin/demo-basic-auth
KongConsumer/demo-basic-auth-consumer
Secret/demo-basic-auth-credential
Ingress/kong-transform-echo -> konghq.com/plugins=demo-basic-auth
```

Configuración efectiva:

```yaml
plugin: basic-auth
config:
  hide_credentials: true
```

El Consumer referenció `demo-basic-auth-credential` y obtuvo:

```text
type: Programmed
status: True
reason: Programmed
message: Object was successfully configured in Kong.
```

## Resultado automatizado

El PipelineRun terminó en `True/Completed`. Sus tres Tasks finalizaron en
`Succeeded` y los pods en `Completed`:

```text
clone-repository
validate-baseline
configure-and-test
```

Evidencia segura:

```text
missing credentials status=401
invalid credentials status=401
valid credentials status=200
control=/demo status=200
control=/demo2 status=200
PASS: credenciales ausentes/invalidas rechazadas, credenciales validas aceptadas y ocultadas
```

## Comparación

| Caso | `/transform` | Resultado |
|---|---:|---|
| Línea base | 200 | Acceso sin autenticación antes del plugin. |
| Sin `Authorization` | 401 | Rechazado por Kong. |
| Credenciales inválidas | 401 | Rechazado por Kong. |
| Credenciales válidas | 200 | Consumer autenticado. |
| Header hacia upstream | Ausente | `hide_credentials=true` aprobado. |
| `/demo` y `/demo2` | 200 | Rutas de control aisladas. |

## Validación externa sin credenciales

```text
HTTP/1.1 401 Unauthorized
www-authenticate: Basic realm="service"
x-kong-response-latency: 0
server: kong/3.9.3
```

```json
{
  "message": "Unauthorized"
}
```

La ausencia de `x-kong-upstream-latency` confirma que Kong rechazó la solicitud
antes de invocar el backend.

## PVC

| Campo | Valor |
|---|---|
| PVC | `pvc-8868dadf4d` |
| Solicitud | 100Mi |
| Capacidad informada | 99Gi |
| Estado | Bound |
| StorageClass | `crc-csi-hostpath-provisioner` |

El PVC contiene el clon y evidencia HTTP, pero no la contraseña.

## Reconciliación

La búsqueda de `error|failed|invalid|rejected` en los logs recientes de KIC no
devolvió resultados.

## Rollback previsto

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-basic-auth -n kong-demo
oc delete kongconsumer demo-basic-auth-consumer -n kong-demo
oc delete secret demo-basic-auth-credential -n kong-demo
```

Después del rollback, `/transform`, `/demo` y `/demo2` deben responder 200 sin
credenciales y el Secret debe dejar de existir.

## Conclusión

P03-02 queda aprobada. Kong aplicó correctamente HTTP Basic, rechazó solicitudes
sin credenciales o con credenciales inválidas, autenticó al Consumer válido,
ocultó `Authorization` al upstream y mantuvo aisladas las rutas de control.
