# Resultado P04-01: Prometheus

## Estado

**Aprobado funcionalmente el 2026-09-02; rollback pendiente.**

Evidencia de consola aportada por el operador en CRC. No se ejecutaron
comandos contra el cluster desde la herramienta de documentación.
La aprobación del ciclo completo requiere registrar el rollback.

## Ejecución

- Gateway: Kong Community 3.9.3, DB-less, una réplica disponible.
- PipelineRun: `kong-plugin-prometheus-mddlm`, `True / Succeeded`.
- Tasks `clone-repository` y `configure-and-test`: `True / Succeeded`.
- Pods de Tasks: Completed, sin reinicios.
- Pod de pruebas: `kong-plugin-prometheus-mddlm-configure-and-test-pod`.
- No se instaló Prometheus Server ni Grafana.

## Evidencia funcional

| Comprobación | Resultado |
|---|---|
| Línea base /transform, /demo y /demo2 | HTTP 200 |
| Endpoint de métricas previo a configuración | PASS del step-baseline |
| kong_http_requests_total, code=200, ruta objetivo | Incremento 10 |
| kong_kong_latency_ms_count, ruta objetivo | Incremento 10 |
| kong_upstream_latency_ms_count, ruta objetivo | Incremento 10 |
| kong_request_latency_ms_count, ruta objetivo | Incremento 10 |
| /demo y /demo2 después de configurar | HTTP 200 |
| Contadores e histogramas por ruta de controles | Sin incremento, validado por el test |
| Buckets y sumas de histogramas; identidad de Gateway | Comprobaciones del test completadas |

Extracto de `step-test`:

```text
control=/demo status=200
control=/demo2 status=200
kong_http_requests_total target_delta=10 expected_min=10
kong_kong_latency_ms_count target_delta=10 expected_min=10
kong_upstream_latency_ms_count target_delta=10 expected_min=10
kong_request_latency_ms_count target_delta=10 expected_min=10
PASS: HTTP counter and latency histograms increased; controls isolated
```

Los incrementos de los histogramas son cantidades de observaciones, no
valores de latencia en milisegundos. No se midieron percentiles ni se
validó almacenamiento histórico.

## Recursos inspeccionados

- `KongPlugin/demo-prometheus` en `kong-demo`:
  `status_code_metrics=true`, `latency_metrics=true`,
  `bandwidth_metrics=false`, `per_consumer=false`,
  `upstream_health_metrics=false`.
- Ingress `kong-transform-echo`: `plugins=demo-prometheus strip-path=true`.
- Service `kong-lab-prometheus-metrics` en `kong`:
  ClusterIP `10.217.4.201`, puerto 8100/TCP.
- EndpointSlice `kong-lab-prometheus-metrics-8qvvn`:
  endpoint `10.217.0.53:8100`, correspondiente al pod activo.
- PVC `pvc-153765792f`: solicitud 100Mi, capacidad informada 99Gi,
  Bound, StorageClass `crc-csi-hostpath-provisioner`.
  La capacidad informada no es una medición del espacio utilizado.
- Logs del KIC consultados con `--since=10m` y filtro
  `error|failed|invalid|rejected`: sin coincidencias.
  El mensaje de selección entre dos pods identificó al activo
  `kong-kong-66cd4f5c6b-9qvpd`, no al antiguo desalojado.

## Observaciones

Los steps baseline y test mostraron un warning al copiar credenciales
Docker desde /tekton/creds hacia /.docker por permiso denegado.
No impidió esta ejecución; no se cambiaron permisos para la prueba.

El desalojo previo por ephemeral-storage se produjo antes de esta ejecución.
Se confirmó recuperación de Kong y DiskPressure=False antes de continuar;
no se determinó el origen del consumo de disco.

No se generaron ni publicaron credenciales. El PVC conserva clon y evidencia
según el diseño de la Pipeline. Este reporte resume las salidas aportadas:
los snapshots .prom no fueron extraídos ni revisados directamente.

## Rollback pendiente

1. Confirmar que la anotación contiene únicamente demo-prometheus.
2. Desasociar el plugin del Ingress.
3. Eliminar KongPlugin/demo-prometheus.
4. Esperar reconciliación y verificar las tres rutas en 200 y logs del KIC.
5. Eliminar Service/kong-lab-prometheus-metrics en kong.
6. Confirmar NotFound para ambos recursos y el Ingress sin plugins.

Conservar PipelineRun y PVC como evidencia; no eliminar el Service
kong-kong-metrics de KIC. El endpoint de Status API puede seguir exponiendo
métricas generales después del rollback.

[Procedimiento PowerShell/Linux](../plugin-tests/prometheus.md#rollback-manual-también-si-falla-la-pipeline).
[Diagrama](../diagrams/prometheus.md).
