# Validación

## Estado de Kong

```bash
helm list -n kong
oc get pods -n kong -o wide
oc get deployment,service,route -n kong
oc get ingressclass kong
```

Se espera un Deployment disponible, un pod `2/2 Running`, la clase `kong` y la Route `kong-proxy`.

## Estado de las aplicaciones

```bash
oc get deployment,pod,service,ingress -n kong-demo
```

## Prueba interna

```bash
oc run curl-test -n kong-demo --image=curlimages/curl:8.12.1 --restart=Never --rm -i -- curl -sS http://kong-echo:5678
```

## Prueba mediante Kong

PowerShell:

```powershell
.\tests\test-kong-proxy.ps1
```

Linux/Bash:

```bash
./tests/test-kong-proxy.sh
```

Los encabezados `server: kong/3.9.3`, `x-kong-upstream-latency`, `x-kong-proxy-latency` y `x-kong-request-id` confirman que la respuesta atravesó Kong.

