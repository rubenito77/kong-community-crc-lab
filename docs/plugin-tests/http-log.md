# P04-02: HTTP Log

Estado: aprobado el 2026-09-02; rollback pendiente.
[Evidencia real](../plugin-test-results/http-log-2026-09-02.md): PipelineRun
kong-plugin-http-log-kb6pm, cinco eventos correlacionados y controles aislados.
Revisión visual completa del mapa aún pendiente; se recibió captura en oscuro.
Kong Community 3.9.x DB-less; solo /transform. No instalar Prometheus, Loki ni Grafana.

## Diseño y evidencia

El operador instala el receptor temporal (Deployment, Service ClusterIP y
ConfigMap en kong-demo). Tekton conserva su RBAC existente: no recibe permisos
para desplegar aplicaciones. El plugin envía eventos JSON asíncronos a /logs.
La prueba espera reconciliación, envía cinco solicitudes GET con marcadores
únicos y consulta /events hasta 45 segundos. Comprueba método, path, HTTP 200,
presencia de Route/Service y tres latencias no negativas. Las rutas /demo y
/demo2 deben responder 200 sin eventos con sus marcadores durante esa ventana.
No se afirma ausencia de eventos fuera de la ventana ni garantía de entrega
ante caída/reinicio del Gateway. Duplicados por reintento se toleran por ID.

El receptor conserva hasta 1000 eventos sanitizados en memoria y admite objeto
o lote JSON de hasta 1 MiB. Reiniciar su Pod pierde los eventos. No tiene PVC,
token de ServiceAccount ni Route. No implementa autenticación ni NetworkPolicy:
ClusterIP no significa aislamiento frente a otros Pods. Usar solo en este lab,
sin tráfico real o credenciales. No es un recolector de producción.
El plugin retira headers, querystring, URL y campos de identidad del registro;
otros metadatos pueden viajar por HTTP interno. El receptor persiste únicamente
su allowlist (path sin query, marcador de laboratorio, método, estado, presencia
de Route/Service y latencias). No imprime cuerpos ni access logs. El PVC Tekton
conserva clon y summary.json, no eventos crudos. No enviar secretos en URI.

## Preparación PowerShell

Tras merge, git switch main y git pull origin main. Confirmar contexto CRC:

```powershell
oc whoami --show-server
oc get deployment kong-kong -n kong
oc get kongplugin demo-http-log -n kong-demo
oc get deployment,service,configmap -n kong-demo | Select-String http-log
oc get kongplugins.configuration.konghq.com -A
oc get kongclusterplugins.configuration.konghq.com
```

Esperar API crc.testing, Gateway 1/1, plugin NotFound y receptor ausente.
No superponer otros plugins locales/globales de logging durante este laboratorio.
Si ya existen recursos, investigar su propiedad; no sobrescribirlos.

```powershell
foreach ($Name in @('kong-transform-echo','kong-echo','kong-echo-2')) {
    oc get ingress $Name -n kong-demo -o jsonpath='{.metadata.name} plugins={.metadata.annotations.konghq\.com/plugins}'
    Write-Host ''
}
foreach ($Ruta in @('transform','demo','demo2')) {
    curl.exe -k -sS -o NUL -w "$Ruta HTTP %{http_code}`n" "https://kong-proxy-kong.apps-crc.testing/$Ruta"
}
oc auth can-i create kongplugins.configuration.konghq.com --as=system:serviceaccount:kong-demo:kong-plugin-tester -n kong-demo
oc auth can-i patch ingresses.networking.k8s.io --as=system:serviceaccount:kong-demo:kong-plugin-tester -n kong-demo
```

Esperar anotaciones vacías, tres HTTP 200 y permisos yes.

```powershell
oc apply -k .\manifests\plugins\http-log\receiver --dry-run=server
oc apply -k .\manifests\plugins\http-log\receiver
oc rollout status deployment/http-log-receiver -n kong-demo --timeout=120s
oc get endpointslice -n kong-demo -l kubernetes.io/service-name=http-log-receiver
oc apply -f .\manifests\plugins\http-log\kongplugin.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-http-log.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-http-log.yaml
```

El dry-run del plugin no lo instala; su creación corresponde a Tekton.
Si falla validación, permisos, imagen o conectividad: detener y diagnosticar,
no ampliar SCC/RBAC ni abrir una Route para resolverlo.

## Ejecución

```powershell
$PIPELINE_RUN = oc create -f .\pipelines\runs\http-log-run.yaml -o jsonpath='{.metadata.name}'
Write-Host "PipelineRun HTTP Log: [$PIPELINE_RUN]"
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
# Ctrl+C tras True; no cancela el PipelineRun.
oc get taskrun,pod -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN"
$TEST_POD = oc get pod -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN,tekton.dev/pipelineTask=configure-and-test" -o jsonpath='{.items[0].metadata.name}'
oc logs $TEST_POD -n kong-demo -c step-baseline
oc logs $TEST_POD -n kong-demo -c step-test
oc get kongplugin demo-http-log -n kong-demo -o yaml
oc get pvc -n kong-demo -l kong-lab/plugin=http-log
oc logs deployment/kong-kong -n kong -c ingress-controller --since=10m | Select-String 'error|failed|invalid|rejected'
```

Esperar True y PASS de cinco eventos y controles aislados. La prueba no está
aprobada hasta obtener esta evidencia real. No volver a ejecutar sin rollback.
Si falla, conservar TaskRuns y PVC; examinar el Step fallido y logs de Kong
proxy por problemas de cola/DNS. El receptor no imprime eventos deliberadamente.

## Rollback manual (también tras fallo parcial)

Verificar que la anotación contiene solamente demo-http-log antes de quitarla.
Si contiene otros plugins, detener y revisar; no borrar asociaciones ajenas.

```powershell
oc get ingress kong-transform-echo -n kong-demo -o jsonpath='{.metadata.annotations.konghq\.com/plugins}'
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-http-log -n kong-demo --ignore-not-found
Start-Sleep -Seconds 30
foreach ($Ruta in @('transform','demo','demo2')) {
    curl.exe -k -sS -o NUL -w "$Ruta HTTP %{http_code}`n" "https://kong-proxy-kong.apps-crc.testing/$Ruta"
}
oc logs deployment/kong-kong -n kong -c ingress-controller --since=5m | Select-String 'error|failed|invalid|rejected'
oc delete -k .\manifests\plugins\http-log\receiver --ignore-not-found
oc get kongplugin demo-http-log -n kong-demo
oc get deployment http-log-receiver -n kong-demo
oc get service http-log-receiver -n kong-demo
oc get configmap http-log-receiver-code -n kong-demo
oc get ingress kong-transform-echo -n kong-demo -o jsonpath='plugins={.metadata.annotations.konghq\.com/plugins} strip-path={.metadata.annotations.konghq\.com/strip-path}'
```

Esperar tres HTTP 200, KIC sin errores, recursos NotFound y plugins vacío con
strip-path=true. Eliminar el receptor pierde su memoria; preservar antes el
resumen de Tekton. Pipeline, PipelineRun y PVC se conservan como evidencia.
No se usa finally para permitir inspección; el rollback es obligatorio.
En Bash, los comandos oc son iguales usando rutas con `/`; usar `sleep 30` y
`curl -ksS -o /dev/null -w '%{http_code}\n' URL` para las comprobaciones HTTP.

## Diagramas y fuentes

- [Mermaid](../diagrams/http-log.md).
- [Archify HTML](../archify/http-log.architecture.html), [JSON](../archify/http-log.architecture.json), [recibo](../archify/http-log.delivery.json).
- [HTTP Log oficial](https://developer.konghq.com/plugins/http-log/).
- [Schema Kong 3.9.1](https://github.com/Kong/kong/blob/3.9.1/kong/plugins/http-log/schema.lua).

Regenerar: `node scripts/archify/build.mjs ../archify-renderer http-log`.
Usa la misma revisión fijada del piloto. Interfaz fija del visor en inglés;
contenido del mapa en español. No genera mapas durante Tekton.
