# P04-03 — OpenTelemetry

Estado: **Preparado; pendiente de prueba en CRC**. No hay resultado aprobado todavía.

## Objetivo y alcance

Validar exportación OTLP/HTTP desde Kong Community 3.9.3 DB-less hacia un
Collector oficial temporal. No requiere instalar Jaeger, Grafana ni un servicio
externo. El Collector recibe Protobuf y exporta OTLP JSON a un sidecar por loopback.
El sidecar conserva solamente un resumen permitido en memoria. Tekton consulta
ese resumen y guarda los resultados agregados en su PVC.

| Caso | Resultado esperado |
|---|---|
| Línea base en las tres rutas | HTTP 200 |
| Cinco GET a `/transform` con `traceparent` W3C | Cinco trace IDs correlacionados |
| Span raíz `kong` | Parent ID recibido, GET, 200, `/transform`, duración positiva |
| Span `kong.balancer` | Hijo del span raíz; duración positiva |
| `/demo` y `/demo2` con sus propios trace IDs | HTTP 200; sin exportación durante 45 s |
| Reinicio del sidecar o pérdida de buffer | Prueba falla; no declarar aislamiento |

Los spans miden operaciones de Kong; sus duraciones no son equivalentes exactos
de los contadores de latencia de Prometheus ni se restan para deducir latencia.
Echo no tiene SDK: no se afirma tracing distribuido dentro de la aplicación.
No se prueba reintento ante caída del Collector ni persistencia de trazas.

## Seguridad y recursos

- Collector `otel/opentelemetry-collector:0.145.0`, versión fijada.
- Deployment `otel-lab-collector`: Collector y sidecar Python; UID asignado por
  OpenShift, sin privilegios, filesystem de solo lectura, sin token de SA.
- Service ClusterIP: `4318` para OTLP y `8080` para lectura de evidencia.
  La ingestión JSON del sidecar usa `127.0.0.1:8081`, no se expone en el Service.
- ConfigMap `otel-lab-config`; sin Secret, Route, PVC propio ni backend externo.
- Solo tráfico sintético sin credenciales. Los spans originales pueden contener
  IP/URL en memoria y en el salto interno Kong→Collector; no enviar datos reales.
- No exporter `debug`/`file`, ni volcados de cuerpos/cabeceras. El sidecar conserva
  IDs de prueba, nombres permitidos, método, ruta permitida, estado y duración.
  Buffer de 4000 spans; cuerpos de ingestión limitados a 2 MiB.
- Servicio interno sin autenticación ni TLS: exclusivo del laboratorio CRC,
  no apto para una instalación compartida/producción sin controles adicionales.
- Se conserva el RBAC existente de `kong-plugin-tester`. El usuario instala el
  Collector y ajusta el Deployment de Kong; Tekton no recibe esos permisos.
- La Pipeline no hace rollback automático: conserva recursos para inspección
  incluso si falla. No repetir sin limpiar primero.

## 1. Preparación y estado original

Ejecutar desde el repositorio, después de revisar/fusionar el PR:

```powershell
Set-Location C:\Users\Ruben\kong-community-crc-lab
git switch main
git pull origin main
oc whoami --show-server
oc get deployment kong-kong -n kong
oc get kongplugins.configuration.konghq.com -A
oc get kongclusterplugins.configuration.konghq.com
oc get deployment,service,configmap -n kong-demo -l kong-lab/plugin=opentelemetry
foreach ($Name in @('kong-transform-echo','kong-echo','kong-echo-2')) {
    oc get ingress $Name -n kong-demo -o jsonpath='{.metadata.name} plugins={.metadata.annotations.konghq\.com/plugins}'
    Write-Host ''
}
foreach ($Ruta in @('transform','demo','demo2')) {
    curl.exe -k -sS -o NUL -w "$Ruta HTTP %{http_code}`n" "https://kong-proxy-kong.apps-crc.testing/$Ruta"
}
```

Esperado: API CRC, Kong 1/1, ningún plugin, ningún recurso OTel, anotaciones
vacías y rutas 200. Detenerse si hay configuraciones ajenas; no sobrescribirlas.

### Instrumentación temporal del Gateway

En esta sesión el usuario comprobó que no había variables explícitas
`KONG_*TRACING` en los contenedores; añadió las dos variables siguientes al
contenedor `proxy` y confirmó rollout, nuevo Pod 2/2 y las tres rutas 200.
Esto es evidencia de **preparación**, no aprobación del plugin.

Comprobar el estado antes de cualquier cambio:

```powershell
$KongDeployment = oc get deployment kong-kong -n kong -o json | ConvertFrom-Json
$KongDeployment.spec.template.spec.containers |
    Where-Object name -eq 'proxy' |
    ForEach-Object { $_.env } |
    Where-Object { $_.name -match '^KONG_.*TRACING' } |
    Select-Object name, value, valueFrom
```

Si ya aparecen `all` y `1.0`, **no repetir el cambio**. Para una ejecución nueva,
registrar previamente las variables existentes y cualquier `envFrom`/configuración
Helm. Si había otros valores, diseñar su restauración exacta, no eliminarlos.
Solo para el estado original comprobado sin ambas variables:

```powershell
oc set env deployment/kong-kong -n kong --containers=proxy KONG_TRACING_INSTRUMENTATIONS=all KONG_TRACING_SAMPLING_RATE=1.0 --dry-run=server
oc set env deployment/kong-kong -n kong --containers=proxy KONG_TRACING_INSTRUMENTATIONS=all KONG_TRACING_SAMPLING_RATE=1.0
oc rollout status deployment/kong-kong -n kong --timeout=180s
```

Este cambio temporal provoca un rollout y deriva de los valores Helm. No ejecutar
un upgrade Helm durante la prueba. `all`/100 % tiene coste para todo el Gateway;
retirar ambas variables al finalizar, también ante una prueba fallida.

## 2. Instalar Collector y Pipeline

```powershell
oc auth can-i create kongplugins.configuration.konghq.com --as=system:serviceaccount:kong-demo:kong-plugin-tester -n kong-demo
oc auth can-i patch ingresses.networking.k8s.io --as=system:serviceaccount:kong-demo:kong-plugin-tester -n kong-demo
oc apply -k .\manifests\plugins\opentelemetry\collector --dry-run=server
oc apply -k .\manifests\plugins\opentelemetry\collector
oc rollout status deployment/otel-lab-collector -n kong-demo --timeout=180s
oc get deployment otel-lab-collector -n kong-demo
oc get endpointslice -n kong-demo -l kubernetes.io/service-name=otel-lab-collector
oc apply -f .\manifests\plugins\opentelemetry\kongplugin.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-opentelemetry.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-opentelemetry.yaml
```

Esperado: ambos permisos `yes`, Collector 1/1 y Pod 2/2. Su readiness TCP solo
comprueba el listener; el warmup de Tekton exige recepción real de un span raíz.
El dry-run del KongPlugin no lo instala: la Pipeline lo crea después de la línea base.
Si falla el rollout, inspeccionar eventos y logs `-c collector`; no cambiar SCC ni
ejecutar como root para sortear el error.

## 3. Ejecutar una vez

```powershell
Remove-Variable PIPELINE_RUN -ErrorAction SilentlyContinue
$PIPELINE_RUN = oc create -f .\pipelines\runs\opentelemetry-run.yaml -o jsonpath='{.metadata.name}'
Write-Host "PipelineRun OpenTelemetry: [$PIPELINE_RUN]"
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

Salir de la observación con Ctrl+C tras `True / Succeeded`; no crea otra ejecución.

```powershell
oc get taskrun,pod -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN"
$TEST_POD = oc get pod -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN,tekton.dev/pipelineTask=configure-and-test" -o jsonpath='{.items[0].metadata.name}'
oc logs $TEST_POD -n kong-demo -c step-baseline
oc logs $TEST_POD -n kong-demo -c step-test
```

Esperado, no evidencia observada aún:

```text
control=/demo status=200
control=/demo2 status=200
target traces=5 W3C parent=valid root/balancer durations=positive
PASS: OTLP traces correlated; controls isolated during 45s observation
```

## 4. Evidencia segura

```powershell
oc get kongplugin demo-opentelemetry -n kong-demo -o yaml
oc get ingress kong-transform-echo -n kong-demo -o jsonpath='plugins={.metadata.annotations.konghq\.com/plugins} strip-path={.metadata.annotations.konghq\.com/strip-path}'
oc get deployment otel-lab-collector -n kong-demo
oc get pvc -n kong-demo -l kong-lab/plugin=opentelemetry -o custom-columns='NAME:.metadata.name,REQUESTED:.spec.resources.requests.storage,CAPACITY:.status.capacity.storage,STATUS:.status.phase,STORAGECLASS:.spec.storageClassName'
oc logs deployment/kong-kong -n kong -c ingress-controller --since=10m | Select-String -Pattern 'error|failed|invalid|rejected'
oc logs deployment/otel-lab-collector -n kong-demo -c collector --since=10m
```

Revisar también errores de exportación del contenedor `proxy` localmente; no pegar
líneas con URLs privadas ni credenciales. Registrar el resultado real en un PR
separado, sin convertir expectativas o pruebas unitarias en evidencia CRC.

## 5. Rollback

Después de guardar la evidencia, verificar que la anotación es exclusivamente
`demo-opentelemetry`. No retirar asociaciones de otros laboratorios.

```powershell
oc get ingress kong-transform-echo -n kong-demo -o jsonpath='{.metadata.annotations.konghq\.com/plugins}'
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-opentelemetry -n kong-demo
Start-Sleep -Seconds 45
foreach ($Ruta in @('transform','demo','demo2')) {
    curl.exe -k -sS -o NUL -w "$Ruta HTTP %{http_code}`n" "https://kong-proxy-kong.apps-crc.testing/$Ruta"
}
oc delete -k .\manifests\plugins\opentelemetry\collector
```

Esto elimina Collector, sidecar, Service y ConfigMap; los spans en memoria se
pierden. Se conservan Pipeline, PipelineRuns y PVC de evidencia. No eliminar pods
antiguos de Kong como parte de este rollback.

Restaurar **solo las dos variables añadidas en esta sesión**:

```powershell
oc set env deployment/kong-kong -n kong --containers=proxy KONG_TRACING_INSTRUMENTATIONS- KONG_TRACING_SAMPLING_RATE-
oc rollout status deployment/kong-kong -n kong --timeout=180s
oc get deployment kong-kong -n kong
$KongDeployment = oc get deployment kong-kong -n kong -o json | ConvertFrom-Json
$KongDeployment.spec.template.spec.containers | Where-Object name -eq 'proxy' | ForEach-Object { $_.env } | Where-Object { $_.name -match '^KONG_.*TRACING' } | Select-Object name, value, valueFrom
oc get kongplugin demo-opentelemetry -n kong-demo
oc get deployment otel-lab-collector -n kong-demo
oc get service otel-lab-collector -n kong-demo
oc get configmap otel-lab-config -n kong-demo
oc get ingress kong-transform-echo -n kong-demo -o jsonpath='plugins={.metadata.annotations.konghq\.com/plugins} strip-path={.metadata.annotations.konghq\.com/strip-path}'
foreach ($Ruta in @('transform','demo','demo2')) {
    curl.exe -k -sS -o NUL -w "$Ruta HTTP %{http_code}`n" "https://kong-proxy-kong.apps-crc.testing/$Ruta"
}
oc logs deployment/kong-kong -n kong -c ingress-controller --since=5m | Select-String -Pattern 'error|failed|invalid|rejected'
```

Esperado: Kong 1/1, ninguna de las dos variables, cuatro `NotFound`, Ingress limpio
y tres HTTP 200. No usar `rollout undo`: podría revertir cambios ajenos.

## Validación local y diagramas

```powershell
python -m unittest discover -s tests -v
```

Pruebas unitarias del parser, límites, aislamiento tardío, correlación, reinicios,
evicción y flujo simulado. No sustituyen la ejecución del Collector ni de CRC.

- [Mermaid](../diagrams/opentelemetry.md).
- [Archify](../archify/opentelemetry.architecture.html),
  [JSON](../archify/opentelemetry.architecture.json),
  [revisión](../archify/opentelemetry.review.md).
- [Plugin Kong 3.9.3: esquema](https://github.com/Kong/kong/blob/3.9.3/kong/plugins/opentelemetry/schema.lua).
- [Instrumentación Kong 3.9.3](https://github.com/Kong/kong/blob/3.9.3/kong/observability/tracing/instrumentation.lua).
- [Collector 0.145.0: distribución](https://github.com/open-telemetry/opentelemetry-collector-releases/blob/v0.145.0/distributions/otelcol/manifest.yaml).
- [Exporter OTLP HTTP/JSON](https://github.com/open-telemetry/opentelemetry-collector/blob/v0.145.0/exporter/otlphttpexporter/README.md).
