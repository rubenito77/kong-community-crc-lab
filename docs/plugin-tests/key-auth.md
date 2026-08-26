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

## Detalle de validación, instalación y seguridad

1. `oc apply -k .\pipelines\rbac --dry-run=server` valida ServiceAccount, Role y
   RoleBinding sin persistir cambios.
2. `oc apply -k .\pipelines\rbac` concede al ServiceAccount permisos limitados
   al namespace para `KongPlugin`, `KongConsumer`, Ingress y Secret.
3. Los dos comandos `oc apply` de la Pipeline primero validan y después instalan
   `Pipeline/kong-plugin-key-auth`.
4. `oc create` genera un PipelineRun nuevo y captura su nombre.
5. `validate-baseline` exige `/transform` en 200 antes de protegerla.
6. El step de configuración genera una clave aleatoria, la escribe con modo 600
   en un `emptyDir`, crea `Secret/demo-key-auth-credential`, aplica el Consumer y
   el Plugin, y anota el Ingress.
7. El step de prueba exige 401 sin clave, 401 con clave inválida y 200 con la
   clave válida. También confirma que `hide_credentials=true` evita reenviar el
   header `apikey` al upstream y que `/demo` y `/demo2` siguen en 200.

```powershell
oc auth can-i create kongconsumers.configuration.konghq.com --as=system:serviceaccount:kong-demo:kong-plugin-tester -n kong-demo
oc auth can-i create secrets --as=system:serviceaccount:kong-demo:kong-plugin-tester -n kong-demo
```

Ambos deben devolver `yes`; comprueban autorización efectiva sin crear recursos.
No se debe ejecutar `oc get secret ... -o yaml` en una captura o log compartido:
el valor Base64 es reversible. Para inspección segura use:

```powershell
oc get secret demo-key-auth-credential -n kong-demo -o go-template='name={{.metadata.name}}{{"\n"}}type={{.type}}{{"\n"}}keys={{range $key,$value := .data}}{{$key}} {{end}}{{"\n"}}'
oc get kongconsumer demo-key-auth-consumer -n kong-demo -o yaml
oc get kongplugin demo-key-auth -n kong-demo -o yaml
```

El rollback respeta dependencias: desasocia el plugin, elimina `KongPlugin`,
elimina `KongConsumer` y finalmente el Secret. `/transform` debe regresar a 200
sin requerir `apikey`.

## Fuentes oficiales

- [Key Authentication con KIC](https://developer.konghq.com/kubernetes-ingress-controller/get-started/key-authentication/)
- [Carga de recursos por IngressClass](https://developer.konghq.com/kubernetes-ingress-controller/ingress/)
