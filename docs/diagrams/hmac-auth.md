# Flujo: HMAC Authentication

```mermaid
flowchart TD
  C["Cliente /transform"] --> H{"Authorization HMAC"}
  H -->|Ausente| E1["HTTP 401"]
  H -->|Firma inválida| E2["HTTP 401"]
  H -->|Fecha vencida| E3["HTTP 401"]
  H -->|Firma y fecha válidas| U["Upstream HTTP 200"]
```

```mermaid
flowchart TD
  PR["PipelineRun"] --> ED["emptyDir con username y secret"]
  PR --> PVC["PVC con clon y evidencia"]
  ED --> SEC["Secret hmac-auth"]
  SEC --> CON["KongConsumer"]
  CON --> PL["KongPlugin hmac-auth"]
  PL --> ING["Ingress /transform"]
  ED --> PY["Python firma HMAC-SHA256 en memoria"]
```

La Pipeline firma únicamente `date`, exige una ventana de 30 segundos y elimina
el material efímero al terminar. `hide_credentials=true` evita que el header
`Authorization` llegue al upstream.
