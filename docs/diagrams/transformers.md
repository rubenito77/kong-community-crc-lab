# Flujo: Request y Response Transformers

```mermaid
sequenceDiagram
  participant C as Cliente
  participant K as Kong /transform
  participant U as Backend observable
  C->>K: GET /transform
  Note over K: request-transformer agrega<br/>X-Lab-Request-Transform
  K->>U: GET / + header agregado
  U-->>K: JSON con headers recibidos
  Note over K: response-transformer agrega<br/>X-Lab-Response-Transform
  K-->>C: HTTP 200 + header de respuesta
```

```mermaid
flowchart TD
  P[PipelineRun + PVC] --> B[Baseline sin headers]
  B --> RQ[Crear request-transformer<br/>y anotar Ingress]
  RQ --> TQ[Validar header dentro del JSON upstream]
  TQ --> RS[Crear response-transformer<br/>asociar ambos plugins]
  RS --> TS[Validar header del cliente<br/>y rutas de control]
```

Usa dos `KongPlugin`, RBAC de Plugin/Ingress y PVC. No usa Secret, Consumer ni
`emptyDir`. El backend observable es necesario para demostrar la transformación
de la solicitud. El rollback desasocia ambos plugins y conserva la aplicación.
