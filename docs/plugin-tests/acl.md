# Prueba P03-04: ACL con Key Authentication

## Objetivo

Proteger `/transform` mediante autenticación por API key y autorización por
grupo ACL. Un Consumer pertenece a `acl-allowed`; el segundo pertenece a
`acl-denied`.

## Recursos

- `KongPlugin/demo-acl-key-auth`: identifica al Consumer y oculta `apikey`.
- `KongPlugin/demo-acl`: permite solamente el grupo `acl-allowed` y oculta
  `X-Consumer-Groups`.
- Dos `KongConsumer`, uno permitido y otro denegado.
- Dos Secrets `key-auth` con claves aleatorias.
- Dos Secrets `acl` con las membresías de grupo.

## Casos

| Caso | Resultado esperado |
|---|---:|
| Línea base sin plugins | 200 |
| Sin API key | 401 |
| API key inválida | 401 |
| Consumer permitido | 200 |
| Consumer fuera del grupo | 403 |
| `apikey` en upstream | Ausente |
| `X-Consumer-Groups` en upstream | Ausente |
| `/demo` y `/demo2` | 200 |

Las API keys se generan dentro del Pod, se comparten por `emptyDir` y nunca se
imprimen ni se escriben en el PVC. Los Secrets permanecen hasta el rollback.

## PowerShell

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-acl.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-acl.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\acl-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

## Linux

```bash
oc apply -f pipelines/pipelines/kong-plugin-acl.yaml --dry-run=server
oc apply -f pipelines/pipelines/kong-plugin-acl.yaml
PIPELINE_RUN="$(oc create -f pipelines/runs/acl-run.yaml -o jsonpath='{.metadata.name}')"
oc get pipelinerun "$PIPELINE_RUN" -n kong-demo -w
```

## Inspección segura

No se debe usar `-o yaml` ni mostrar `.data` para los cuatro Secrets. Para
listar únicamente metadatos:

```powershell
oc get secret -n kong-demo -l app.kubernetes.io/part-of=kong-community-crc-lab -o custom-columns='NAME:.metadata.name,TYPE:.type,CREDENTIAL:.metadata.labels.konghq\.com/credential'
oc get kongconsumer demo-acl-allowed-consumer demo-acl-denied-consumer -n kong-demo
oc get kongplugin demo-acl-key-auth demo-acl -n kong-demo
```

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-acl-key-auth demo-acl -n kong-demo
oc delete kongconsumer demo-acl-allowed-consumer demo-acl-denied-consumer -n kong-demo
oc delete secret demo-acl-allowed-key demo-acl-denied-key demo-acl-allowed-group demo-acl-denied-group -n kong-demo
```

## Fuentes oficiales

- [ACL con Kong Ingress Controller](https://developer.konghq.com/kubernetes-ingress-controller/acl/)
- [Plugin ACL](https://developer.konghq.com/plugins/acl/)
- [Plugin Key Authentication](https://developer.konghq.com/plugins/key-auth/)
