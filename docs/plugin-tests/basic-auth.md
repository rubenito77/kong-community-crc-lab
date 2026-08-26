# Prueba P03-02: Basic Authentication

## Objetivo

Proteger `/transform` con autenticación HTTP Basic. El usuario de laboratorio y
la contraseña se crean durante el PipelineRun; la contraseña no se almacena en
Git, parámetros, PVC, evidencia ni logs.

## Recursos y casos

- `KongPlugin/demo-basic-auth` con `hide_credentials=true`.
- `KongConsumer/demo-basic-auth-consumer`.
- `Secret/demo-basic-auth-credential` etiquetado como `basic-auth`.

| Caso | Resultado esperado |
|---|---:|
| Línea base sin plugin | 200 |
| Sin `Authorization` | 401 |
| Usuario/contraseña inválidos | 401 |
| Usuario/contraseña válidos | 200 |
| Header recibido por upstream | Ausente |
| `/demo` y `/demo2` | 200 |

## Recursos Tekton

El PVC comparte repositorio y evidencia no sensible entre Tasks. Un `emptyDir`
comparte usuario/contraseña solamente entre los Steps `configure` y `test` del
mismo Pod. El archivo se elimina al finalizar y el volumen desaparece con el Pod.

El RBAC ya aplicado para `key-auth` permite administrar `KongConsumer` y Secret
únicamente dentro de `kong-demo`; no se agregan permisos de cluster.

## Validación e instalación en PowerShell

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-basic-auth.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-basic-auth.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\basic-auth-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

`--dry-run=server` valida sin persistir; `apply` instala la Pipeline; `create`
genera una ejecución independiente y `-w` observa su condición.

## Validación e instalación en Linux

```bash
oc apply -f pipelines/pipelines/kong-plugin-basic-auth.yaml --dry-run=server
oc apply -f pipelines/pipelines/kong-plugin-basic-auth.yaml
PIPELINE_RUN="$(oc create -f pipelines/runs/basic-auth-run.yaml -o jsonpath='{.metadata.name}')"
oc get pipelinerun "$PIPELINE_RUN" -n kong-demo -w
```

## Inspección segura

```powershell
oc get kongplugin demo-basic-auth -n kong-demo -o yaml
oc get kongconsumer demo-basic-auth-consumer -n kong-demo -o yaml
oc get secret demo-basic-auth-credential -n kong-demo -o custom-columns='NAME:.metadata.name,TYPE:.type,CREDENTIAL_TYPE:.metadata.labels.konghq\.com/credential'
```

No se debe imprimir `.data.password`: Base64 es reversible.

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-basic-auth -n kong-demo
oc delete kongconsumer demo-basic-auth-consumer -n kong-demo
oc delete secret demo-basic-auth-credential -n kong-demo
```

Se desasocia primero para restaurar el tráfico; luego se eliminan Plugin,
Consumer y finalmente la credencial. Las tres rutas deben responder 200.

## Resultado real

P03-02 fue aprobada el 2026-08-26 mediante el PipelineRun
`kong-plugin-basic-auth-rxq7f`. La evidencia no contiene usuario ni contraseña.
Véase [Resultado de Basic Authentication](../plugin-test-results/basic-auth-2026-08-26.md).

## Fuentes oficiales

- [Múltiples métodos de autenticación con KIC](https://developer.konghq.com/kubernetes-ingress-controller/multiple-auth-methods/)
- [Carga de recursos por IngressClass](https://developer.konghq.com/kubernetes-ingress-controller/ingress/)
