# Prueba P01-04: IP Restriction

## Descubrimiento de la IP efectiva

El backend recibió `X-Forwarded-For: 192.168.127.1, 10.217.0.2`, pero Kong
registró la conexión como `10.217.0.2`. No existen variables explícitas
`KONG_TRUSTED_IPS`, `KONG_REAL_IP_HEADER` ni `KONG_REAL_IP_RECURSIVE`.

Un Pod Tekton atravesando la Route pública también fue registrado como
`10.217.0.2`, por lo que la prueba usa `10.217.0.2/32`.

## Casos

| Etapa | Configuración | `/transform` |
|---|---|---:|
| Línea base | Sin plugin | 200 |
| Denegación | `deny: 10.217.0.2/32` | 403 |
| Permiso | `allow: 10.217.0.2/32` | 200 |

`/demo` y `/demo2` permanecen en HTTP 200. La Pipeline usa la Route pública,
no el Service interno, para conservar el recorrido real.

## PowerShell

```powershell
oc apply -f .\pipelines\pipelines\kong-plugin-ip-restriction.yaml --dry-run=server
oc apply -f .\pipelines\pipelines\kong-plugin-ip-restriction.yaml
$PIPELINE_RUN = oc create -f .\pipelines\runs\ip-restriction-run.yaml -o jsonpath='{.metadata.name}'
oc get pipelinerun $PIPELINE_RUN -n kong-demo -w
```

## Linux

```bash
oc apply -f pipelines/pipelines/kong-plugin-ip-restriction.yaml --dry-run=server
oc apply -f pipelines/pipelines/kong-plugin-ip-restriction.yaml
PIPELINE_RUN="$(oc create -f pipelines/runs/ip-restriction-run.yaml -o jsonpath='{.metadata.name}')"
oc get pipelinerun "$PIPELINE_RUN" -n kong-demo -w
```

## Rollback

```powershell
oc annotate ingress kong-transform-echo -n kong-demo konghq.com/plugins-
oc delete kongplugin demo-ip-deny demo-ip-allow -n kong-demo
```

## Fuentes oficiales

- [Deny IP range](https://developer.konghq.com/plugins/ip-restriction/examples/deny/)
- [Allow IP and range](https://developer.konghq.com/plugins/ip-restriction/examples/allow/)
