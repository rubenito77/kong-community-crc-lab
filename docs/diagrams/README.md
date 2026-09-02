# Diagramas del laboratorio de plugins

Esta carpeta explica gráficamente la plataforma, dónde se configura cada
plugin y qué recursos temporales o persistentes necesita cada Pipeline.

## Índice

- [Arquitectura general y ciclo de vida](platform-and-plugin-lifecycle.md)
- [Rate Limiting](rate-limiting.md)
- [Correlation ID](correlation-id.md)
- [Request y Response Transformers](transformers.md)
- [CORS](cors.md)
- [Request Size Limiting](request-size-limiting.md)
- [Request Termination](request-termination.md)
- [IP Restriction](ip-restriction.md)
- [Key Authentication](key-auth.md)
- [Basic Authentication](basic-auth.md)
- [JWT HS256](jwt.md)
- [ACL con Key Authentication](acl.md)
- [HMAC Authentication](hmac-auth.md)

- [Prometheus](prometheus.md)

## Dependencias comparadas

| Prueba | Ingress objetivo | KongPlugin | Consumer | Secret | PVC Tekton | `emptyDir` | RBAC especial |
|---|---|---:|---:|---:|---:|---:|---|
| Rate Limiting | `kong-echo` | Sí | No | No | Sí | No | KongPlugin + Ingress |
| Correlation ID | `kong-echo` | Sí | No | No | Sí | No | KongPlugin + Ingress |
| Transformers | `kong-transform-echo` | 2 | No | No | Sí | No | KongPlugin + Ingress |
| CORS | `kong-transform-echo` | Sí | No | No | Sí | No | KongPlugin + Ingress |
| Request Size Limiting | `kong-transform-echo` | Sí | No | No | Sí | No | KongPlugin + Ingress |
| Request Termination | `kong-transform-echo` | Sí | No | No | Sí | No | KongPlugin + Ingress |
| IP Restriction | `kong-transform-echo` | 2 | No | No | Sí | No | KongPlugin + Ingress |
| Key Authentication | `kong-transform-echo` | Sí | Sí | Sí | Sí | Sí | Agrega KongConsumer + Secret |
| Basic Authentication | `kong-transform-echo` | Sí | Sí | Sí | Sí | Sí | Reutiliza KongConsumer + Secret |
| JWT HS256 | `kong-transform-echo` | 2 | Sí | Sí | Sí | Sí | Reutiliza KongConsumer + Secret |
| ACL + Key Authentication | `kong-transform-echo` | 2 | 2 | 4 | Sí | Sí | Reutiliza KongConsumer + Secret |
| HMAC Authentication | `kong-transform-echo` | Sí | Sí | Sí | Sí | Sí | Reutiliza KongConsumer + Secret |
| Prometheus | `kong-transform-echo` | Sí | No | No | Sí | No | RBAC existente; Service manual en kong |

El PVC pertenece al PipelineRun y comparte el repositorio clonado y la evidencia
entre Tasks. `emptyDir` se usa solamente para pasar una credencial efímera entre
Steps del mismo Pod sin escribirla en Git, parámetros, logs ni PVC.
