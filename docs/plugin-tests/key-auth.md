# Prueba P03-01: Key Authentication

## Objetivo

Proteger `/transform` mediante una API key generada durante el PipelineRun.
La credencial no se almacena en Git, parámetros ni logs.

## Recursos

- `KongPlugin/demo-key-auth` con header `apikey` y `hide_credentials=true`.
- `KongConsumer/demo-key-auth-consumer`.
- `Secret/demo-key-auth-credential`, generado por Tekton y etiquetado
  `konghq.com/credential=key-auth`.

## Casos

| Caso | Resultado |
|---|---:|
| Línea base sin plugin ni key | 200 |
| Sin key después de proteger | 401 |
| Key inválida | 401 |
| Key válida generada | 200 |
| Key recibida por upstream | Ausente |
| `/demo` y `/demo2` | 200 |

La clave se comparte entre los Steps mediante un `emptyDir` efímero y el
archivo se elimina al terminar. El Secret permanece para inspección porque
`cleanup=false`, pero su valor no debe mostrarse ni incorporarse a evidencia.

## PowerShell

```powershell
oc apply -k .\pipelines\rbac --dry-run=server
oc apply -k .\pipelines\rbac
oc apply -f .\pipelines\pipelines\kong-plugin-key-auth.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-key-auth.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\key-auth-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-key-auth -n kong-demo
oc delete kongconsumer demo-key-auth-consumer -n kong-demo
oc delete secret demo-key-auth-credential -n kong-demo
```

## Fuentes oficiales

- [Key Authentication con KIC](https://developer.konghq.com/kubernetes-ingress-controller/get-started/key-authentication/)
- [Carga de recursos por IngressClass](https://developer.konghq.com/kubernetes-ingress-controller/ingress/)
