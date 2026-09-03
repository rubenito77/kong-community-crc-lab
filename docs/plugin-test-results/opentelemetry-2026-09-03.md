# P04-03 — OpenTelemetry: resultado 2026-09-03

Estado: **aprobado; rollback pendiente**.

## Procedencia y ejecuciones

Evidencia de consola PowerShell aportada por Rubén en CRC
(`https://api.crc.testing:6443`). El agente no ejecutó estas pruebas en el cluster.
La implementación se integró mediante PR #43 y la corrección mediante PR #44.
El usuario actualizó main a `08cf78c` antes de repetir. No se aportó la salida
del SHA exacto clonado por Tekton; no se atribuye un commit al PipelineRun.

| Ejecución | Resultado | Alcance |
|---|---|---|
| `kong-plugin-opentelemetry-4zkk8` | Failed / StepFailed | Falló la comparación de ruta en step-test; las Tasks/Steps previos completaron |
| `kong-plugin-opentelemetry-gdlch` | True / Succeeded | Cinco trazas correlacionadas y controles aislados durante 45 s |

En la ejecución aprobada, las Tasks `clone-repository` y `configure-and-test`
mostraron `True / Succeeded`. Ambos Pods terminaron `Completed` con cero reinicios.
El Pod de prueba fue `kong-plugin-opentelemetry-gdlch-configure-and-test-pod`.
La duración indicada del PipelineRun fue aproximadamente 63 segundos.

## Resultados observados

| Comprobación | Resultado |
|---|---|
| Línea base `/transform`, `/demo`, `/demo2` | HTTP 200 |
| Endpoint de evidencia accesible | PASS |
| Trazas objetivo correlacionadas | 5 trace IDs distintos |
| Parent ID W3C del span raíz | Validado por la prueba |
| Span raíz `kong` | GET, 200, ruta lógica `/transform`, duración positiva |
| Span `kong.balancer` | Parent ID del span raíz y duración positiva |
| `/demo` y `/demo2` | HTTP 200 |
| Exportación de los trace IDs de control | Ninguna detectada durante 45 s |
| Reinicio del sidecar/evicción del buffer durante observación | No detectados por las comprobaciones del test |
| Resultado final | PASS |

Salida del Step test:

```text
baseline /transform status=200
baseline /demo status=200
baseline /demo2 status=200
control=/demo status=200
control=/demo2 status=200
target traces=5 W3C parent=valid root/balancer durations=positive
PASS: OTLP traces correlated; controls isolated during 45s observation
```

Los Steps baseline/test mostraron un warning de copia de credenciales `.docker`
hacia `/`, por permiso denegado. Se registra como advertencia no bloqueante para
esta ejecución; no se afirma que esté solucionada.

Cinco trazas no significa cinco spans ni entrega exactamente una vez. El
verificador deduplica por span ID. El aislamiento se limita a los trace IDs y a
la ventana observada. No se probaron spans internos de la aplicación (sin SDK),
un backend de visualización, persistencia, ni caída/reintentos del Collector.
Las duraciones de spans no se equiparan a métricas de latencia de Prometheus.

## Corrección aplicada

El fallo inicial ocurrió en `root.get("route") == "/transform"`. El filtro
original descartaba los patrones de ruta de KIC como `/transform/`. La corrección
normaliza únicamente nueve cadenas explícitas de las tres rutas y conserva el
patrón permitido como `route_pattern`, sin aceptar prefijos arbitrarios ni
ejecutar expresiones regulares recibidas.

Antes de repetir, el usuario confirmó el rollout del Collector y la presencia
de la tabla corregida en su contenedor `evidence`. El nuevo resultado PASS valida
el escenario corregido. La consola del fallo no incluía el atributo original;
no se inventa su valor ni se declara aprobada aquella ejecución.

## Configuración y estado final verificados

- KongPlugin `demo-opentelemetry`, generación 1; creado `2026-09-03T14:23:22Z`.
- Plugin `opentelemetry`; resource `service.name=kong-otel-lab`; muestreo `1`.
- Propagación: extract/inject `w3c`, default_format `w3c`.
- Endpoint interno: `http://otel-lab-collector.kong-demo.svc.cluster.local:4318/v1/traces`.
- Queue: max_batch_size 20, max_coalescing_delay 1, max_retry_time 15.
- Timeouts: connect 1000, send 3000 y read 3000 ms.
- Ingress: `plugins=demo-opentelemetry strip-path=true`.
- Collector: Pod `otel-lab-collector-6c74cd8f9b-2fzkm`, 2/2 Running,
  cero reinicios, edad aproximada 11 minutos en la inspección final.
- Collector `--since=10m`: sin mensajes en la salida aportada.
- KIC `--since=10m`: sin coincidencias con `error|failed|invalid|rejected` en
  el Pod seleccionado `kong-kong-7cd8cd786c-jc9r5`. El aviso `Found 2 pods`
  informa la selección; no es un error de reconciliación. No cubre los otros
  Pods ni los logs del contenedor proxy.

## PVC conservados

| Nombre | Solicitado | Capacidad reportada | Estado | StorageClass |
|---|---|---|---|---|
| `pvc-4806180c28` | 100Mi | 99Gi | Bound | crc-csi-hostpath-provisioner |
| `pvc-ad7d29e013` | 100Mi | 99Gi | Bound | crc-csi-hostpath-provisioner |

La salida fue filtrada por `kong-lab/plugin=opentelemetry`; no incluye la
relación de cada PVC con un PipelineRun. No se asignan nombres a ejecuciones.
La capacidad reportada no representa espacio consumido. No se leyó el contenido
de los PVC; el resumen agregado está previsto por el código del test.

## Rollback pendiente

Todavía permanecen el plugin asociado, Collector/sidecar, Service y ConfigMap.
Durante la preparación se confirmaron en el proxy:

- `KONG_TRACING_INSTRUMENTATIONS=all`.
- `KONG_TRACING_SAMPLING_RATE=1.0`.

No se aportó evidencia de su retirada. Tras integrar este resultado, seguir el
[rollback de la guía](../plugin-tests/opentelemetry.md#5-rollback): desasociar el
Ingress, eliminar el plugin, dar tiempo a las colas, validar rutas, retirar el
Collector y eliminar únicamente las dos variables añadidas. Esperar el rollout
de Kong y volver a comprobar 1/1, tres HTTP 200, anotación vacía, recursos
retirados y ausencia de ambas variables. No usar rollout undo.

Conservar las dos ejecuciones y los PVC. Retirar el Collector elimina sus trazas
temporales en memoria. No eliminar Pods antiguos de Kong en esta operación.
El cierre del rollback se documentará después de recibir sus salidas reales.

## Diagramas y referencias

- [Guía](../plugin-tests/opentelemetry.md).
- [Mermaid](../diagrams/opentelemetry.md).
- [Mapa Archify](../archify/opentelemetry.architecture.html).
- [Fuente Archify](../archify/opentelemetry.architecture.json) y
  [revisión del mapa](../archify/opentelemetry.review.md).

La topología no cambia por este resultado. La aprobación del test no sustituye
la revisión visual del mapa ni modifica sus recibos de generación.
