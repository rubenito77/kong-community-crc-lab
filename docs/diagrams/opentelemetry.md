# Flujo: OpenTelemetry

Estado: preparado; pendiente de ejecutar y validar en CRC.

```mermaid
flowchart TD
  T["Tekton: solicitudes W3C"] -->|"HTTP /transform"| K["Kong Gateway instrumentado"]
  C["KongPlugin + Ingress"] -.->|"Configuración KIC"| K
  K -->|"HTTP con traceparent"| A["Echo sin SDK de trazas"]
  K -.->|"OTLP/HTTP Protobuf"| O["Collector temporal"]
  O -.->|"OTLP JSON por loopback"| E["Sidecar: resumen en memoria"]
  T -->|"GET /events"| E
  T -->|"Resumen permitido"| P["PVC de evidencia"]
```

El plugin se asocia solamente a `/transform`; `/demo` y `/demo2` son controles.
La instrumentación temporal `all` y el muestreo `1.0` afectan al Gateway, pero
la exportación se configura por Ingress. La prueba verifica spans de Kong y
`kong.balancer`, no spans internos de la aplicación ni un panel de visualización.

- [Guía y rollback](../plugin-tests/opentelemetry.md).
- [Mapa Archify](../archify/opentelemetry.architecture.html).
- [Fuente Archify](../archify/opentelemetry.architecture.json).
