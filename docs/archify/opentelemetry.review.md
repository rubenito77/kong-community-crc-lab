# Revisión Archify: OpenTelemetry

- Tipo: architecture; versión fijada en [archify.lock.json](archify.lock.json).
- [Fuente JSON](opentelemetry.architecture.json), [HTML](opentelemetry.architecture.html)
  y [recibo](opentelemetry.delivery.json).
- specification_sha256: 4a331b525ac32ac206ac1fce0a6159dc55aadb9d54783c6f11286b03bf5da59f.
- specification_bytes: 2026.
- artifact_sha256: 4a5d24913e7e681ca0bd350739ecd099b2c70a052c1e25802b33508a7ec67901.
- artifact_bytes: 705443.
- Validación: 9/9 showcase, cero errores y advertencias; `deliver` exit 0.
- correction_rounds: 1; dos etiquetas verticales desplazadas según diagnóstico.
- browser_evidence: skipped; `visual-check` exit 2, Chrome/Chromium no disponible.
- Revisión perceptual: pendiente; no se inspeccionó el HTML renderizado.

Antes de aprobar visualmente, abrir en claro/oscuro y comprobar 1440×900,
1600×1000, 1920×1080 y 2048×1320. La aprobación de CRC/HTTP Log no aprueba
este mapa. Contenido en español; controles fijos y `html lang` en inglés por
fallback del visor. No hay animación ni preset alternativo por defecto.

Fuentes de la topología:

- [KongPlugin](../../manifests/plugins/opentelemetry/kongplugin.yaml).
- [Collector y sidecar](../../manifests/plugins/opentelemetry/collector/deployment.yaml).
- [Pipeline](../../pipelines/pipelines/kong-plugin-opentelemetry.yaml).
- [Prueba](../../tests/opentelemetry_lab.py).
- [Mermaid](../diagrams/opentelemetry.md) y [guía](../plugin-tests/opentelemetry.md).

El mapa representa tráfico interno de Tekton, no acceso por la Route pública.
La consulta `/events` y el PVC se explican en la tarjeta para no cruzar el flujo
principal. El Collector no escribe el PVC: lo hace Tekton. La aplicación no tiene
SDK de trazas. No es un mapa del estado actual del cluster ni prueba de ejecución.
