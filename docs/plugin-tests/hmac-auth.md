# Prueba P03-05: HMAC Authentication

## Objetivo

Proteger `/transform` mediante firmas HTTP HMAC-SHA256 y comprobar autenticación,
integridad de la firma y protección contra replay mediante el header `Date`.

## Configuración

- Algoritmo permitido: `hmac-sha256`.
- Header firmado y obligatorio: `date`.
- Tolerancia temporal: 30 segundos.
- `hide_credentials=true`.
- Consumer y credencial HMAC generada por Tekton.

## Casos

| Caso | Resultado esperado |
|---|---:|
| Línea base sin plugin | 200 |
| Sin firma | 401 |
| Firma inválida | 401 |
| Firma válida con fecha vencida | 401 |
| Firma válida y fecha vigente | 200 |
| `Authorization` en upstream | Ausente |
| `/demo` y `/demo2` | 200 |

El username y el secret se generan dentro del Pod. Se comparten entre Steps por
`emptyDir` y no se imprimen ni se escriben en el PVC.

## PowerShell

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-hmac-auth.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-hmac-auth.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\hmac-auth-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

## Linux

```bash
oc apply -f pipelines/pipelines/kong-plugin-hmac-auth.yaml --dry-run=server
oc apply -f pipelines/pipelines/kong-plugin-hmac-auth.yaml
PIPELINE_RUN="$(oc create -f pipelines/runs/hmac-auth-run.yaml -o jsonpath='{.metadata.name}')"
oc get pipelinerun "$PIPELINE_RUN" -n kong-demo -w
```

## Inspección segura

No se debe mostrar el Secret mediante `-o yaml`, `.data` ni columnas que
incluyan `.data`.

```powershell
oc get secret demo-hmac-auth-credential -n kong-demo -o custom-columns='NAME:.metadata.name,TYPE:.type,CREDENTIAL:.metadata.labels.konghq\.com/credential'
oc get kongconsumer demo-hmac-auth-consumer -n kong-demo -o yaml
oc get kongplugin demo-hmac-auth -n kong-demo -o yaml
```

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-hmac-auth -n kong-demo
oc delete kongconsumer demo-hmac-auth-consumer -n kong-demo
oc delete secret demo-hmac-auth-credential -n kong-demo
```

## Fuentes oficiales

- [HMAC Authentication](https://developer.konghq.com/plugins/hmac-auth/)
- [Configuración HMAC](https://developer.konghq.com/plugins/hmac-auth/reference/)
