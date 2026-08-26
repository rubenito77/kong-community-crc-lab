# Flujo: IP Restriction

```mermaid
flowchart LR
  C[Cliente o Pod Tekton] --> R[Router OpenShift]
  R -->|conexión vista como 10.217.0.2| K[Kong]
  K --> D{Regla activa}
  D -->|deny 10.217.0.2/32| E[HTTP 403]
  D -->|allow 10.217.0.2/32| U[Upstream] --> OK[HTTP 200]
```

```mermaid
flowchart TD
  P[PipelineRun + PVC] --> B[Baseline 200]
  B --> KD[Crear demo-ip-deny<br/>anotar Ingress]
  KD --> TD[Validar 403]
  TD --> KA[Crear demo-ip-allow<br/>reemplazar anotación]
  KA --> TA[Validar 200]
```

Usa dos `KongPlugin`, PVC y RBAC para Plugin/Ingress. No usa Consumer, Secret ni
`emptyDir`. El CIDR es específico del recorrido de este CRC; debe descubrirse
nuevamente en otro cluster. El rollback elimina la asociación y ambos CR.
