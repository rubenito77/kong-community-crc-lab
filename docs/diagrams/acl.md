# Flujo: ACL con Key Authentication

```mermaid
flowchart TD
  C["Cliente /transform"] --> K{"API key válida"}
  K -->|No| E1["HTTP 401"]
  K -->|Sí| A{"Grupo acl-allowed"}
  A -->|No| E2["HTTP 403"]
  A -->|Sí| U["Upstream HTTP 200"]
```

```mermaid
flowchart TD
  PR["PipelineRun"] --> ED["emptyDir con dos API keys"]
  PR --> PVC["PVC con clon y evidencia"]
  ED --> S["Secrets key-auth"]
  G["Secrets ACL con grupos"] --> C["Dos KongConsumer"]
  S --> C
  C --> P["Plugins key-auth y ACL"]
  P --> I["Ingress /transform"]
```

`key-auth` se ejecuta antes de ACL: primero identifica al Consumer y después
ACL compara sus grupos con `allow: acl-allowed`. Las claves no llegan al
upstream y `hide_groups_header=true` evita reenviar la membresía.
