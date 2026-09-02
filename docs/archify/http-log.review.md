# Revisión Archify: HTTP Log

- Tipo: architecture; Archify fijado por archify.lock.json.
- [JSON](http-log.architecture.json), [HTML](http-log.architecture.html),
  [recibo de generación](http-log.delivery.json).
- specification_sha256: 0309b5134a10adddae88a686b06a822c78130c1c6f3f55ac2b7cd9f554e39e66.
- artifact_sha256: 7a2855832465cf069421e1b606cfa48af8934a5596c6c90d52060cbf58e1b7f4.
- Validación: 9/9 showcase, cero errores y advertencias.
- correction_rounds: 1 (dos etiquetas verticales desplazadas según diagnóstico).
- browser_evidence: skipped; visual-check terminó con salida 2, Chrome no disponible.
- Revisión perceptual: pendiente; no se inspeccionó HTML en navegador.

Revisar claro/oscuro y 1440×900, 1600×1000, 1920×1080, 2048×1320 antes
de aprobar visualmente. La aceptación del mapa CRC no valida este otro mapa.
Los controles del visor usan fallback inglés; contenido en español.

La topología refleja [plugin](../../manifests/plugins/http-log/kongplugin.yaml),
[receptor](../../manifests/plugins/http-log/receiver),
[Pipeline](../../pipelines/pipelines/kong-plugin-http-log.yaml) y
[prueba](../../tests/http_log.py). La flecha receptor→evidencia resume la
consulta que hace Tekton: el receptor no monta ni escribe el PVC.
El diagrama muestra el tráfico interno de Tekton; no incluye navegador/Route
OpenShift porque Tekton accede al Service del proxy. No prueba estado del cluster.
