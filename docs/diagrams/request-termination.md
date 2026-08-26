# Flujo: Request Termination

```mermaid
flowchart LR
  C[GET /transform] --> K[Kong]
  K --> RT[request-termination]
  RT --> E[HTTP 503 + mensaje controlado]
  RT -. no invoca .-> U[Backend observable]
  CTRL[/demo y /demo2] --> OK[HTTP 200]
```

La ausencia de `x-kong-upstream-latency` durante el 503 demuestra que Kong
finaliza la solicitud. Usa PVC y RBAC para Plugin/Ingress; no usa Consumer,
Secret ni `emptyDir`. Al quitar la anotación, el Ingress permanece y Kong vuelve
a enviar `/transform` al backend, recuperando HTTP 200.
