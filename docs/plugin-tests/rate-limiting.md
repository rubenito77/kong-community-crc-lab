# Prueba P01-01: Rate Limiting

## Objetivo y configuración

Limitar `/demo` a cinco solicitudes por minuto y verificar que `/demo2` no sea
afectada. El plugin usa `policy: local`, apropiada para este laboratorio DB-less
de una réplica; el contador reside en la instancia de Kong.

```yaml
plugin: rate-limiting
config:
  minute: 5
  limit_by: ip
  policy: local
  fault_tolerant: true
  hide_client_headers: false
```

## Qué valida la Pipeline

| Tarea | Acción | Criterio de aprobación |
|---|---|---|
| `clone-repository` | Clona la revisión indicada al workspace. | Existen los manifiestos versionados. |
| `validate-baseline` | Consulta `/demo` y `/demo2` antes del cambio. | Ambas responden 200. |
| `apply-plugin` | Aplica el `KongPlugin` y anota `Ingress/kong-echo`. | KIC reconcilia `demo-rate-limit`. |
| `test-rate-limiting` | Envía siete solicitudes a `/demo`. | Aparecen 200 y 429; límite informado = 5. |
| control | Consulta `/demo2`. | Continúa en 200. |

## Instalación y ejecución, comando por comando

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-rate-limiting.yaml --dry-run=server
```

Valida esquema, API `tekton.dev/v1`, namespace y admisión sin crear o modificar
la Pipeline.

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-rate-limiting.yaml
```

Crea la Pipeline o actualiza declarativamente la existente.

```powershell
$PIPELINE_RUN = oc create -f .\pipelines\runs\rate-limiting-run.yaml -o jsonpath='{.metadata.name}'
```

Crea una ejecución nueva mediante `generateName` y guarda su nombre real.

```powershell
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

Observa la condición hasta `True/Completed` o `False/Failed`.

```powershell
oc logs -n kong-demo -l "tekton.dev/pipelineRun=$PIPELINE_RUN" --all-containers=true --prefix=true
```

Agrupa logs de todos los pods y antepone pod/contenedor a cada línea.

## Inspección y rollback

```powershell
oc get kongplugin demo-rate-limit -n kong-demo -o yaml
oc get ingress kong-echo -n kong-demo -o jsonpath='plugins={.metadata.annotations.konghq\.com/plugins}'
```

El primer comando inspecciona la configuración efectiva; el segundo confirma la
asociación, que es lo que activa el plugin para esa ruta.

```powershell
oc annotate ingress kong-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-rate-limit -n kong-demo
```

El sufijo `-` elimina solamente la anotación `konghq.com/plugins`; no elimina el
Ingress. Después se borra el CR ya sin referencias. Finalmente deben validarse
`/demo` y `/demo2` en 200 y la ausencia de errores del controlador.

## Resultado real

Aprobada el 2026-08-24 con `kong-plugin-rate-limiting-nnpv2`. Véase
[evidencia completa](../plugin-test-results/rate-limiting-2026-08-24.md).

## Fuente oficial

- [Rate Limiting](https://developer.konghq.com/plugins/rate-limiting/)
