# Plataforma y ciclo de vida de un plugin

## Recorrido de una solicitud

```mermaid
flowchart LR
  C[Cliente HTTPS] --> OR[Route OpenShift<br/>kong-proxy]
  OR --> KS[Service kong-kong-proxy]
  KS --> KG[Kong Gateway Community<br/>DB-less]
  KIC[Kong Ingress Controller] -->|reconcilia configuración| KG
  I1[Ingress /demo] --> KIC
  I2[Ingress /demo2] --> KIC
  I3[Ingress /transform] --> KIC
  KG -->|/demo| S1[Service kong-echo]
  KG -->|/demo2| S2[Service kong-echo-2]
  KG -->|/transform| S3[Service kong-transform-echo]
  S1 --> P1[Pod echo 1]
  S2 --> P2[Pod echo 2]
  S3 --> P3[Pod observable]
```

El backend no se conecta activamente con Kong. El Ingress declara la ruta y el
Service destino; KIC observa esa declaración y configura Kong.

## Qué ocurre al agregar un plugin

```mermaid
flowchart TD
  G[Manifiesto versionado en Git] --> T[PipelineRun Tekton]
  T --> V[Validación de línea base]
  V --> KP[Crear o actualizar KongPlugin]
  KP --> A[Anotar Ingress<br/>konghq.com/plugins=nombre]
  A --> KIC[KIC detecta ambos recursos]
  KIC --> CFG[Genera configuración DB-less]
  CFG --> KG[Kong aplica el plugin<br/>solo al objeto asociado]
  KG --> TEST[Prueba positiva, negativa<br/>y rutas de control]
```

El `KongPlugin` contiene la configuración. La anotación del Ingress es la
asociación que lo activa para esa ruta. Crear el CR sin anotarlo no modifica el
tráfico del Ingress.

## Qué ocurre al quitar un plugin

```mermaid
flowchart TD
  A[Eliminar anotación<br/>konghq.com/plugins-] --> I[Ingress sigue existiendo]
  I --> KIC[KIC detecta la desasociación]
  KIC --> CFG[Kong elimina el plugin de esa ruta]
  CFG --> FLOW[El tráfico vuelve al flujo normal]
  FLOW --> D[Eliminar KongPlugin]
  D --> C{¿Usa Consumer o Secret?}
  C -->|No| END[Rollback terminado]
  C -->|Sí| DC[Eliminar Consumer]
  DC --> DS[Eliminar Secret]
  DS --> END
```

El sufijo `-` en `konghq.com/plugins-` elimina únicamente la anotación. No
elimina el Ingress, su path, Service, Deployment ni Pod. `strip-path=true`
permanece y Kong continúa quitando el prefijo antes de llamar al backend.

## Recursos de la automatización

```mermaid
flowchart LR
  SA[ServiceAccount<br/>kong-plugin-tester] --> RBAC[Role + RoleBinding<br/>namespace kong-demo]
  RBAC --> API[API Server]
  PR[PipelineRun] --> PVC[PVC workspace<br/>source + evidence]
  PR --> TASKS[Tasks / Pods]
  TASKS --> API
  TASKS -. solo secretos efímeros .-> ED[emptyDir del Pod]
  API --> CR[KongPlugin / Consumer / Secret / Ingress]
```

- El RBAC autoriza a Tekton; no modifica el tráfico por sí mismo.
- El PVC comparte archivos entre Tasks y conserva evidencia del PipelineRun.
- `emptyDir` vive mientras existe el Pod y no se comparte con otros Pods.
- Kong continúa DB-less: los CR Kubernetes son la fuente observada por KIC.
