# Prueba P03-03: JWT HS256

## Objetivo

Proteger `/transform` mediante JWT HS256 y validar token ausente, firma
incorrecta, expiración y token válido. La clave HMAC y los tokens no se guardan
en Git, parámetros, PVC, evidencia ni logs.

## Configuración

```yaml
plugin: jwt
config:
  key_claim_name: iss
  claims_to_verify:
    - exp
  header_names:
    - authorization
```

La credencial JWT exige `algorithm`, `key` y `secret`. `key` identifica la
credencial y debe coincidir con el claim `iss`; `secret` firma mediante HS256.

| Caso | Resultado esperado |
|---|---:|
| Línea base | 200 |
| Sin token | 401 |
| Firma inválida | 401 |
| Token vencido | 401 |
| Token válido | 200 |
| `Authorization` hacia upstream | Ausente |
| `/demo` y `/demo2` | 200 |

## Recursos Tekton y seguridad

El PVC comparte clon y evidencia HTTP. Un `emptyDir` transfiere `key` y `secret`
entre los Steps del mismo Pod. Python genera los JWT en memoria usando únicamente
la biblioteca estándar; no imprime ni persiste tokens. El Secret permanece en
OpenShift hasta el rollback.

## PowerShell

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-jwt.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-jwt.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\jwt-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

## Linux

```bash
oc apply -f pipelines/pipelines/kong-plugin-jwt.yaml --dry-run=server
oc apply -f pipelines/pipelines/kong-plugin-jwt.yaml
PIPELINE_RUN="$(oc create -f pipelines/runs/jwt-run.yaml -o jsonpath='{.metadata.name}')"
oc get pipelinerun "$PIPELINE_RUN" -n kong-demo -w
```

## Inspección segura

```powershell
oc get kongplugin demo-jwt -n kong-demo -o yaml
oc get kongconsumer demo-jwt-consumer -n kong-demo -o yaml
oc get secret demo-jwt-credential -n kong-demo -o custom-columns='NAME:.metadata.name,TYPE:.type,CREDENTIAL_TYPE:.metadata.labels.konghq\.com/credential'
```

No se deben imprimir `.data.key` ni `.data.secret`.

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-jwt -n kong-demo
oc delete kongconsumer demo-jwt-consumer -n kong-demo
oc delete secret demo-jwt-credential -n kong-demo
```

## Fuentes oficiales

- [JWT plugin](https://developer.konghq.com/plugins/jwt/)
- [Verificar claims registrados](https://developer.konghq.com/plugins/jwt/examples/verified-claim/)
- [Recursos cargados por KIC](https://developer.konghq.com/kubernetes-ingress-controller/ingress/)
