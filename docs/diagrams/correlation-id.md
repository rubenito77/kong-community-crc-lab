# Flujo: Correlation ID

```mermaid
flowchart LR
  C[Solicitud /demo] --> H{¿Trae<br/>X-Lab-Correlation-ID?}
  H -->|No| G[Kong genera UUID]
  H -->|Sí| P[Kong preserva valor]
  G --> U[Upstream]
  P --> U
  U --> E[Kong devuelve el ID al cliente]
  C2[/demo2] --> N[Sin plugin<br/>sin header del laboratorio]
```

La Pipeline usa PVC para código/evidencia y RBAC para crear el `KongPlugin` y
anotar `Ingress/kong-echo`. No requiere Secret, Consumer ni `emptyDir`. El
rollback elimina la asociación y el CR; el Ingress continúa encaminando `/demo`.
