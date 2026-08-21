# Operación

## Estado general

```bash
helm status kong -n kong
oc get deployment,pod,service,route -n kong
oc get deployment,pod,service,ingress -n kong-demo
```

## Logs

```bash
oc logs deployment/kong-kong -n kong -c proxy --tail=100
oc logs deployment/kong-kong -n kong -c ingress-controller --tail=100
```

Seguimiento en vivo:

```bash
oc logs deployment/kong-kong -n kong -c ingress-controller -f
```

## Endpoints internos

```bash
oc get endpoints kong-kong-proxy -n kong -o wide
oc get endpoints kong-echo kong-echo-2 -n kong-demo -o wide
```

## Reinicio controlado

El siguiente comando modifica el Deployment y reinicia el pod:

```bash
oc rollout restart deployment/kong-kong -n kong
oc rollout status deployment/kong-kong -n kong --timeout=5m
```

