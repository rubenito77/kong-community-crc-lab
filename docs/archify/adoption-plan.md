# Adopción gradual de Archify

## Acuerdo de trabajo

Conservar los diagramas Mermaid y sumar mapas interactivos a los nuevos
laboratorios. Incorporar los anteriores gradualmente mediante PRs acotados.
No se convierte todo el catálogo en el piloto de arquitectura.

## Secuencia

1. Integrar el piloto CRC con la revisión manual completada.
2. En el próximo laboratorio, añadir el mapa Archify junto con manifiestos,
   Pipeline, guía y Mermaid. No declarar la prueba aprobada antes de ejecutarla.
3. Convertir los laboratorios anteriores por grupos pequeños, revisando cada
   mapa contra los manifiestos y resultados existentes.

## Contenido de cada mapa

- Ingress y ruta afectados; rutas de control.
- Plugin y recursos asociados, si corresponden: Consumer, Secret o Service.
- Separación entre configuración KIC y tráfico HTTP.
- Casos de prueba y resultados esperados, distinguidos de evidencia observada.
- Recursos retirados y conservados durante rollback.
- Enlaces a manifiestos, guía, Mermaid y resultados.

No incluir claves, tokens, firmas ni contenido de Secrets.

## Entrega y validación

Mantener JSON editable y HTML generado, versión fijada de Archify, recibo
de generación y revisión visual. No editar el HTML manualmente.
Enlazar cada mapa desde su guía y los índices.
La generación no ocurre automáticamente al ejecutar Tekton; tampoco es
monitoreo ni descubrimiento del cluster. El script admite crc, http-log y
opentelemetry mediante un selector explícito; el valor por defecto sigue siendo crc.

## Estado inicial

- Arquitectura CRC: implementada en PR #39; revisión manual y matriz
  multirresolución confirmadas por el usuario; automatización skipped.
- Nuevos plugins: incorporación acordada para los siguientes laboratorios.
- HTTP Log: mapa preparado junto al laboratorio; ejecución y revisión visual pendientes.
- Plugins anteriores: conversión pendiente; sus Mermaid se conservan.
- OpenTelemetry: mapa añadido; [prueba CRC aprobada, rollback pendiente](../plugin-test-results/opentelemetry-2026-09-03.md). La revisión visual completa mantiene su estado independiente.
