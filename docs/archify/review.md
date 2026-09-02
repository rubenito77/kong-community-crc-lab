# Recibo de revisión del piloto

## Generación determinista

- Tipo: architecture.
- Herramienta: Archify 2.17.0-dev.1.
- Commit: 06dd052602dd9a369e4d034e24faef0917b5a60c.
- Ejecutor: Node.js 24.19.0.
- Salida: docs/archify/crc.architecture.html.
- Perfil: showcase, 9/9 checks, cero errores y cero advertencias.
- correction_rounds: 2 (composición compacta tras capturas del usuario).
- specification_sha256: 37ae3eddf756e14620e8c5a9a72251f88368725e438ebaa3c43a35c457a7ff71.
- artifact_sha256: fc4d7aee8655688ce4bac16f79271a4a8de490ab5e2bddaf98d810b04a890580.
- Tamaños: JSON 2908 bytes; HTML 712859 bytes.
- ViewBox reducido de 1390×790 a 1100×600 para aumentar la escala
  efectiva del texto; etiquetas recolocadas según diagnósticos.

[Recibo de deliver](delivery.json).

## Navegador y revisión perceptual

- browser_evidence: skipped.
- Motivo del recibo oficial: viewer/chrome-unavailable, salida 2.
- No se midieron viewports ni se obtuvieron capturas automatizadas.
- El usuario aportó capturas del HTML anterior en claro y oscuro y confirmó
  que no veía barra de desplazamiento. Se observó texto pequeño; estas
  capturas no validan el nuevo hash ni todas las resoluciones requeridas.
- La descarga de Chromium se interrumpió después de agotar el tiempo de
  espera; no se usó una captura antigua como evidencia.
- Revisión visual perceptual: pendiente, no aprobada.

Por este motivo el PR se entrega como borrador. Antes de marcarlo listo:

1. Abrir el HTML local en Chrome/Edge y revisar textos y conexiones.
2. Ejecutar visual-check con Chrome/Chromium según la guía.
3. Revisar tema claro y oscuro y las cuatro resoluciones requeridas.
4. Comprobar búsqueda/foco y que el visor cierre sus paneles correctamente.
5. Registrar los resultados vinculados al hash exacto del HTML.

No se modificó OpenShift, no se publicaron sitios ni se instalaron skills
globales. Los diagramas Mermaid y las pruebas de plugins siguen intactos.
