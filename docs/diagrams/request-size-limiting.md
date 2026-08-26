# Flujo: Request Size Limiting

```mermaid
flowchart LR
  C[POST /transform] --> K[Kong mide payload]
  K --> S{¿Tamaño <= 1 KiB?}
  S -->|Sí: 512 bytes| U[Upstream] --> OK[HTTP 200]
  S -->|No: 2048 bytes| E[HTTP 413<br/>sin upstream]
  CTRL[/demo y /demo2] --> COK[HTTP 200]
```

La línea base demuestra que 2048 bytes llegan al backend antes del plugin. La
Pipeline usa PVC y RBAC para Plugin/Ingress; no usa Consumer, Secret ni
`emptyDir`. Tras el rollback, el mismo POST de 2048 bytes vuelve a HTTP 200.
