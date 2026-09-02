# P04-01: Prometheus sin servidor adicional

## Estado y alcance

Preparado; pendiente de ejecución y aprobación en CRC. No hay todavía un
resultado funcional aprobado. La línea base aportada el 2026-09-02 confirmó
Kong 3.9.3, `/status` y `/metrics` en HTTP 200 por el puerto 8100, sin KongPlugin
ni KongClusterPlugin configurados.

El plugin se asocia únicamente a `Ingress/kong-transform-echo` en `kong-demo`.
Se activan `status_code_metrics` y `latency_metrics`; no se instrumentan
Consumers, bandwidth ni upstream health. No se necesita Prometheus Server
ni Grafana: esta prueba no conserva series históricas ni ofrece PromQL.

## Recursos y permisos

| Recurso | Namespace | Responsable |
|---|---|---|
| KongPlugin/demo-prometheus | kong-demo | Pipeline |
| Anotación de kong-transform-echo | kong-demo | Pipeline |
| Service/kong-lab-prometheus-metrics | kong | Operador, instalación manual |
| Pipeline/kong-plugin-prometheus y PipelineRun | kong-demo | Operador |
| PVC nuevo de 100Mi por ejecución | kong-demo | Tekton |

El Service nuevo es ClusterIP y apunta a `8100`, Status API del Gateway.
No modifica `kong-kong-metrics`, cuyos puertos 10255 y 10254 corresponden a KIC.
No expone Admin API ni una Route pública. ClusterIP no equivale a autenticación:
otros workloads con conectividad al Service pueden consultar Status API.
Se reutiliza el RBAC actual de `kong-plugin-tester`, sin permisos nuevos en `kong`.
Si una NetworkPolicy bloquea el acceso entre namespaces, detener la prueba y
revisar su alcance; no eliminar políticas como solución automática.

## Prerrequisitos

- Contexto CRC correcto; nodo Ready, DiskPressure=False y espacio suficiente.
- Exactamente una réplica de Gateway disponible. Las métricas son por nodo;
  este test mediante Service no es válido para múltiples réplicas.
- Las tres rutas en HTTP 200, sin plugins asociados; no hay plugins globales.
- Los recursos `demo-prometheus` y `kong-lab-prometheus-metrics` no existen
  antes de la primera instalación. No sobrescribir recursos ajenos.
- Una sola ejecución por vez y sin tráfico externo de prueba concurrente.
- Cada PipelineRun utiliza un PVC nuevo; nunca se borra un workspace existente.

El 2026-09-02 hubo un desalojo por ephemeral-storage antes de la preparación;
Kong se recuperó y DiskPressure volvió a False. Eso no identifica el origen
del consumo de disco. No borrar PVC/evidencias para liberar espacio sin revisión.

## Preparación PowerShell

```powershell
oc whoami --show-server
oc get deployment kong-kong -n kong
oc get kongplugin -A
oc get kongclusterplugin
oc get service kong-lab-prometheus-metrics -n kong
oc get kongplugin demo-prometheus -n kong-demo
oc auth can-i create kongplugins.configuration.konghq.com --as=system:serviceaccount:kong-demo:kong-plugin-tester -n kong-demo
oc auth can-i patch ingresses.networking.k8s.io --as=system:serviceaccount:kong-demo:kong-plugin-tester -n kong-demo
```

Las dos consultas a recursos específicos deben devolver NotFound antes de
instalarlos; los dos permisos deben responder yes. Confirmar también que las
anotaciones de los tres Ingress están vacías.

```powershell
oc apply -f .\manifests\plugins\prometheus\gateway-metrics-service.yaml --dry-run=server
oc apply -f .\manifests\plugins\prometheus\gateway-metrics-service.yaml
oc get endpointslice -n kong -l kubernetes.io/service-name=kong-lab-prometheus-metrics
oc apply -f .\pipelines\pipelines\kong-plugin-prometheus.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-prometheus.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\prometheus-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

No aplicar manualmente `kongplugin.yaml` antes del PipelineRun: la Pipeline
verifica que no exista y lo crea luego de comprobar la línea base.

```powershell
oc get taskrun,pod -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN"
$TEST_POD = oc get pod -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN,tekton.dev/pipelineTask=configure-and-test" -o jsonpath='{.items[0].metadata.name}'
oc logs $TEST_POD -n kong-demo -c step-baseline
oc logs $TEST_POD -n kong-demo -c step-test
oc get kongplugin demo-prometheus -n kong-demo -o yaml
oc logs deployment/kong-kong -n kong -c ingress-controller --since=10m | Select-String -Pattern 'error|failed|invalid|rejected'
```

## Linux

Se aplican los mismos prerrequisitos y revisión de permisos.

```bash
oc apply -f manifests/plugins/prometheus/gateway-metrics-service.yaml --dry-run=server
oc apply -f manifests/plugins/prometheus/gateway-metrics-service.yaml
oc apply -f pipelines/pipelines/kong-plugin-prometheus.yaml --dry-run=server
oc apply -f pipelines/pipelines/kong-plugin-prometheus.yaml
PIPELINE_RUN=$(oc create -f pipelines/runs/prometheus-run.yaml -o jsonpath='{.metadata.name}')
oc get pipelinerun "$PIPELINE_RUN" -n kong-demo -w
TEST_POD=$(oc get pod -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN,tekton.dev/pipelineTask=configure-and-test" -o jsonpath='{.items[0].metadata.name}')
oc logs "$TEST_POD" -n kong-demo -c step-test
```

## Criterios automáticos y evidencia

| Comprobación | Resultado esperado |
|---|---|
| Línea base de las tres rutas | 200 |
| /metrics y formato | 200, text/plain, muestras válidas y kong_node_info |
| Reconciliación | Series de ruta objetivo aparecen con reintentos acotados |
| 10 solicitudes adicionales a /transform | Incremento >=10 de kong_http_requests_total con code=200 |
| Histogramas Kong, upstream y total | Incremento >=10 de cada _count, presencia de _bucket y _sum |
| Tres solicitudes a cada control | 200 y sin incremento de contadores/histogramas por ruta |
| Identidad del Gateway | Mismo node_id y versión durante la prueba |

Se filtra la etiqueta `route` por los prefijos de KIC para los Ingress del lab:
`kong-demo.kong-transform-echo.`, `kong-demo.kong-echo.` y `kong-demo.kong-echo-2.`.
No se usan las métricas generales de Nginx para demostrar aislamiento.
Un cambio de nombres KIC exige revisar el test; no aceptar métricas ajenas.
El calentamiento y la lectura posterior tienen hasta 30 intentos con pausas
de 2 segundos; cada petición tiene timeout de 15 segundos.

El PVC guarda el clon en `repository/` y evidencia en `evidence/prometheus/`:
snapshots `.prom`, línea base y reporte de incrementos. No se generan credenciales.
Los snapshots contienen nombres internos y métricas del nodo: revisarlos antes
de publicar. El reporte de resultados real se agregará tras recibir evidencia
de ejecución; no se crea un archivo de aprobación anticipada.

## Rollback manual, también si falla la Pipeline

No hay cleanup automático: los recursos se conservan para inspección. No
reintentar un PipelineRun sobre el plugin activo. Primero registrar evidencia
y hacer rollback. Comprobar que el Ingress solo tiene `demo-prometheus`; si
otra persona cambió la anotación, detenerse y preservar sus cambios.

Comandos válidos en PowerShell y Bash desde la raíz del repositorio:

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-prometheus -n kong-demo
```

Esperar reconciliación; confirmar las tres rutas en 200 y KIC sin errores.
En PowerShell:

```powershell
Start-Sleep -Seconds 10
oc get ingress kong-transform-echo -n kong-demo -o jsonpath='plugins={.metadata.annotations.konghq\.com/plugins} strip-path={.metadata.annotations.konghq\.com/strip-path}'
foreach ($Ruta in @('transform', 'demo', 'demo2')) {
    curl.exe -k -sS -o NUL -w "$Ruta HTTP %{http_code}`n" "https://kong-proxy-kong.apps-crc.testing/$Ruta"
}
oc logs deployment/kong-kong -n kong -c ingress-controller --since=5m | Select-String -Pattern 'error|failed|invalid|rejected'
```

En Bash:

```bash
sleep 10
oc get ingress kong-transform-echo -n kong-demo -o jsonpath='plugins={.metadata.annotations.konghq\.com/plugins} strip-path={.metadata.annotations.konghq\.com/strip-path}'
for route in transform demo demo2; do
  curl -k -sS -o /dev/null -w "$route HTTP %{http_code}\n" "https://kong-proxy-kong.apps-crc.testing/$route"
done
oc logs deployment/kong-kong -n kong -c ingress-controller --since=5m
```

El endpoint /metrics puede seguir respondiendo 200 con métricas generales:
no debe exigirse 404 ni reiniciarse Kong para borrar contadores históricos.
Antes de eliminar el Service se puede inspeccionar el endpoint por port-forward:

```powershell
oc port-forward -n kong service/kong-lab-prometheus-metrics 18100:8100
```

En otra terminal consultar `curl.exe -sS http://127.0.0.1:18100/metrics`
(usar `curl` en Linux), luego cerrar port-forward con Ctrl+C.
Finalizar eliminando únicamente el Service temporal:

```powershell
oc delete service kong-lab-prometheus-metrics -n kong
oc get kongplugin demo-prometheus -n kong-demo
oc get service kong-lab-prometheus-metrics -n kong
```

Los dos recursos deben devolver NotFound. Conservar PipelineRun/PVC como
evidencia hasta acordar una limpieza explícita. El Service y el plugin se
pueden recrear desde Git; eliminar el Service no borra métricas de memoria.

## Fuentes y diagrama

- [Diagrama del laboratorio](../diagrams/prometheus.md)
- [Plugin Prometheus oficial](https://developer.konghq.com/plugins/prometheus/)
- [Schema exacto Kong 3.9.3](https://github.com/Kong/kong/blob/3.9.3/kong/plugins/prometheus/schema.lua)
- [Exporter exacto Kong 3.9.3](https://github.com/Kong/kong/blob/3.9.3/kong/plugins/prometheus/exporter.lua)
