# Flujo: Basic Authentication

```mermaid
flowchart LR
  C[Cliente /transform] --> K[Kong basic-auth]
  K --> H{Authorization Basic}
  H -->|Ausente| E1[HTTP 401]
  H -->|Usuario o password inválidos| E2[HTTP 401]
  H -->|Válidos| CO[KongConsumer]
  CO --> U[Upstream HTTP 200]
  K -. hide_credentials=true .-> X[Authorization no llega al upstream]
```

```mermaid
flowchart TD
  SA[ServiceAccount Tekton] --> RBAC[RBAC namespace kong-demo<br/>Consumer + Secret]
  PR[PipelineRun] --> PVC[PVC: clon + evidencia]
  PR --> POD[Pod configure-and-test]
  POD --> GEN[Genera password aleatorio]
  GEN --> ED[emptyDir efímero]
  GEN --> SEC[Secret basic-auth<br/>username + password]
  SEC --> CON[KongConsumer]
  CON --> PL[KongPlugin basic-auth]
  PL --> ING[Ingress /transform]
  ED --> TEST[Pruebas 401 / 401 / 200]
```

Reutiliza el RBAC incorporado para `key-auth`. El PVC nunca contiene la
contraseña; `emptyDir` la comparte dentro del Pod y el Secret la mantiene para
KIC/Kong hasta el rollback. El orden de baja es Ingress, Plugin, Consumer y Secret.
