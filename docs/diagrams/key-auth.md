# Flujo: Key Authentication

```mermaid
flowchart LR
  C[Cliente /transform] --> K[Kong key-auth]
  K --> H{Header apikey}
  H -->|Ausente| E1[HTTP 401]
  H -->|Inválido| E2[HTTP 401]
  H -->|Válido| CO[KongConsumer]
  CO --> U[Upstream HTTP 200]
  K -. hide_credentials=true .-> X[apikey no llega al upstream]
```

## Creación segura de la credencial

```mermaid
flowchart TD
  SA[ServiceAccount Tekton] --> RBAC[Role namespace kong-demo<br/>KongConsumer + Secret]
  PR[PipelineRun] --> PVC[PVC: repositorio + evidencia]
  PR --> POD[Pod configure-and-test]
  POD --> GEN[Step configure genera API key]
  GEN --> ED[emptyDir modo efímero]
  GEN --> SEC[Secret key-auth en API Server]
  SEC --> CON[KongConsumer referencia Secret]
  CON --> PL[KongPlugin key-auth]
  PL --> ING[Ingress plugins=demo-key-auth]
  ED --> TEST[Step test lee key sin imprimirla]
  TEST --> DEL[Elimina archivo efímero]
```

`key-auth` es la primera prueba que amplía el RBAC para `KongConsumer` y Secret.
El PVC no contiene la clave; solamente conserva el clon y evidencia no sensible.
El `emptyDir` comparte la clave entre Steps del mismo Pod y desaparece con él.
El Secret persiste hasta el rollback para que KIC/Kong puedan autenticar.

## Rollback

```mermaid
flowchart LR
  A[Quitar anotación] --> P[Eliminar KongPlugin]
  P --> C[Eliminar KongConsumer]
  C --> S[Eliminar Secret]
  S --> V[Validar /transform, /demo y /demo2 = 200]
```

El orden elimina primero el efecto sobre el tráfico y después las dependencias.
La eliminación del Secret borra definitivamente la API key del cluster.
