# Flujo: CORS

```mermaid
flowchart TD
  B[Navegador] --> O{Origin}
  O -->|cliente-lab.example| M{Método}
  M -->|OPTIONS preflight| PF[Kong responde permisos CORS<br/>sin upstream]
  M -->|GET| U[Upstream /transform]
  U --> RH[Respuesta con<br/>Access-Control-Allow-Origin]
  O -->|origen no autorizado| NR[No se autoriza ese origen<br/>el navegador bloquea acceso]
  CTRL[/demo y /demo2] --> NC[Sin headers CORS]
```

La Pipeline usa PVC y RBAC para `KongPlugin`/Ingress. No necesita Consumer,
Secret ni `emptyDir`. `preflight_continue=false` permite que Kong resuelva el
preflight. El rollback quita la anotación y elimina `demo-cors`; `/transform`
continúa en HTTP 200 pero sin headers `Access-Control-*`.
