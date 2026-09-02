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

- browser_evidence: skipped (automatización).
- Motivo del recibo oficial: viewer/chrome-unavailable, salida 2.
- No se midieron viewports ni se obtuvieron capturas automatizadas.
- Revisión manual de la versión compacta: capturas aportadas por Rubén en
  tema claro y oscuro, con componentes completos y sin solapamientos visibles.
- Tras solicitar pruebas de búsqueda, zoom y apertura/cierre de paneles,
  Rubén confirmó: «funciona correctamente».
- Después de solicitar la matriz 1440×900, 1600×1000, 1920×1080 y
  2048×1320 en ambos temas, Rubén confirmó: «funciono correctamente continuemos».
- Resultado multirresolución: satisfactorio según reporte manual del usuario;
  no se recibieron capturas adicionales por resolución.
- La revisión corresponde a la versión entregada en el commit
  0e82d89d835ce2dd9d098f1ee6c47477a53a2d52. El hash del HTML generado figura
  arriba; no se midió el hash de la copia local del usuario.
- Revisión perceptual manual: satisfactoria para las capturas recibidas.
- Validación multirresolución manual: confirmada por el usuario.
- Validación automatizada: skipped; no se declara aprobada.

## Cierre de revisión del piloto

La revisión manual solicitada queda cerrada según las capturas previas y la
confirmación del usuario. El HTML no cambia en este cierre documental.
La comprobación automatizada con visual-check sigue sin ejecutarse por falta
de Chrome y se mantiene registrada por separado; no se equipara a una prueba
automatizada aprobada.

No se modificó OpenShift, no se publicaron sitios ni se instalaron skills
globales. Los diagramas Mermaid y las pruebas de plugins siguen intactos.
