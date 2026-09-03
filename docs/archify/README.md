# Piloto Archify: arquitectura CRC

Complemento de los diagramas Mermaid existentes; no los reemplaza.
El mapa es documentación de arquitectura, no descubrimiento ni monitoreo
del cluster. No representa plugins temporales ya revertidos, PostgreSQL,
Prometheus Server ni Grafana.

## Mapas de plugins

- [HTTP Log](http-log.architecture.html): [guía](../plugin-tests/http-log.md),
  [JSON](http-log.architecture.json) y [recibo](http-log.delivery.json).
  Preparado; revisión visual y prueba en CRC pendientes.
  Generar con `node scripts/archify/build.mjs ../archify-renderer http-log`.
- [OpenTelemetry](opentelemetry.architecture.html): [guía](../plugin-tests/opentelemetry.md),
  [JSON](opentelemetry.architecture.json), [recibo](opentelemetry.delivery.json) y
  [revisión pendiente](opentelemetry.review.md).
  Generar con `node scripts/archify/build.mjs ../archify-renderer opentelemetry`.

Este estilo se puede incorporar gradualmente a cada laboratorio, conservando
Mermaid. Cada mapa deberá documentar dónde se aplica el plugin, el flujo de
prueba y el estado tras rollback. Ejecutar Tekton no genera estos mapas:
se mantienen como JSON y se regeneran con el script indicado abajo.
Este piloto solo incluye la arquitectura base; no convierte los plugins anteriores.

El [plan de adopción](adoption-plan.md) define la secuencia y los criterios
para nuevos plugins y conversiones anteriores.

## Abrir el mapa

Después del merge y de actualizar el clon, en PowerShell:

```powershell
Start-Process .\docs\archify\crc.architecture.html
```

En Linux con escritorio:

```bash
xdg-open docs/archify/crc.architecture.html
```

También se puede abrir el archivo directamente desde el explorador.
GitHub muestra el código HTML, no ejecuta este visor dentro del README.
No se habilita GitHub Pages ni se publica un sitio en este PR.

El contenido del diagrama está en español; la interfaz fija del visor
y su atributo HTML lang usan el fallback inglés de Archify.
El visor abre sin animación automática y ofrece tema claro/oscuro,
zoom y herramientas interactivas propias del paquete.

## Interpretación

- Camino principal: navegador → Router OpenShift, configurado por la Route
  kong-proxy → Service kong-kong-proxy → Kong Gateway → backend según path.
- Las flechas discontinuas representan observación/configuración, no tráfico
  del cliente. KIC no es un salto del recorrido HTTP.
- Cada caja inferior agrupa Service y Pod para mantener legible el mapa.
  Es una relación lógica: no afirma que cada paquete atraviese una ClusterIP;
  la resolución y el balanceo pueden usar directamente los endpoints.
- El router termina TLS edge; el tramo mostrado hacia Kong usa HTTP.
- La Admin API utilizada por KIC es local al Pod, no pública.
- Las etiquetas de namespace describen ubicación; no prueban aislamiento
  de red ni existencia de NetworkPolicies.
- Deployment, EndpointSlice, RBAC y Tekton se omiten del mapa compacto;
  sus funciones siguen documentadas en las guías existentes.

## Fuentes y trazabilidad

Base del piloto: commit
`308550c3e3dc6c83ef5c37935bfabe99e8f80848` del repositorio.
No se consultó el cluster para generar este artefacto.

| Elemento | Evidencia |
|---|---|
| Route edge y Service destino | [route.yaml](../../manifests/kong/route.yaml) |
| DB-less, KIC habilitado y proxy ClusterIP | [values-db-less.yaml](../../helm/kong/values-db-less.yaml) |
| /demo y puerto 5678 | [Ingress](../../manifests/apps/kong-echo/ingress.yaml), [Service](../../manifests/apps/kong-echo/service.yaml) |
| /demo2 y puerto 5678 | [Ingress](../../manifests/apps/kong-echo-2/ingress.yaml), [Service](../../manifests/apps/kong-echo-2/service.yaml) |
| /transform y puerto 8080 | [Ingress](../../manifests/apps/kong-transform-echo/ingress.yaml), [Service](../../manifests/apps/kong-transform-echo/service.yaml) |
| Apps y cargas desplegadas | [Manifiestos de aplicaciones](../../manifests/apps) |
| Puertos proxy y relación KIC/Gateway | [Arquitectura](../architecture.md) y relevamiento de consola aportado el 2026-09-02 |
| Estado tras rollback Prometheus | [Resultado P04-01](../plugin-test-results/prometheus-2026-09-02.md) |

Los enlaces relativos muestran la revisión consultada del repositorio.
Para comparar con la base exacta, usar el sourceRevision del
[lock](archify.lock.json) en GitHub. El piloto no activa la opción SRC de
Archify; esta tabla es la trazabilidad documental revisada.

## Regenerar

Requisitos: Git y Node.js; para este piloto se utilizó Node 24.
Archify declara Node >=18, pero se recomienda una versión mantenida.
No requiere npm install, agente de IA, token GitHub, kubeconfig ni acceso a
OpenShift para compilar el JSON existente. Crear o modificar el modelo con
un agente tiene los requisitos y condiciones de ese agente.

Descargar una copia de Archify fuera del repositorio, fijada al commit
registrado. El paquete fijado se identifica como 2.17.0-dev.1: es una
revisión de desarrollo, no una promesa de estabilidad.
Ejemplo PowerShell, desde la raíz del laboratorio (el directorio destino
debe ser nuevo):

```powershell
git clone https://github.com/tt-a1i/archify.git ..\archify-renderer
git -C ..\archify-renderer checkout --detach 06dd052602dd9a369e4d034e24faef0917b5a60c
node .\scripts\archify\build.mjs ..\archify-renderer
```

En Bash:

```bash
git clone https://github.com/tt-a1i/archify.git ../archify-renderer
git -C ../archify-renderer checkout --detach 06dd052602dd9a369e4d034e24faef0917b5a60c
node scripts/archify/build.mjs ../archify-renderer
```

Editar únicamente [crc.architecture.json](crc.architecture.json) para
cambiar el mapa. El script comprueba versión y checkout limpio, valida el
modelo y genera el HTML mediante deliver, que conserva el último HTML válido
si falla la validación. Actualiza [delivery.json](delivery.json) con hashes.
No editar manualmente el HTML generado.

El script desactiva la comprobación remota de actualizaciones mediante
`ARCHIFY_UPDATE_CHECK_DISABLED=1`. La descarga inicial requiere acceso a
GitHub; la generación posterior usa el checkout local y no necesita APIs
de modelos. No se instala una skill global, una GitHub App ni un workflow.
La incorporación de actualizaciones será manual y revisada por PR.

## Validación en navegador

La validación determinista no sustituye una revisión visual. Con Chrome
o Chromium instalado, en PowerShell:

```powershell
$env:ARCHIFY_UPDATE_CHECK_DISABLED = "1"
# Si Chrome no se detecta, definir ARCHIFY_CHROME con la ruta real a chrome.exe.
node ..\archify-renderer\archify\bin\archify.mjs visual-check .\docs\archify\crc.architecture.html --json
```

En Linux:

```bash
ARCHIFY_UPDATE_CHECK_DISABLED=1 node ../archify-renderer/archify/bin/archify.mjs visual-check docs/archify/crc.architecture.html --json
```

Se generan capturas y un recibo local junto al HTML. Revisar ambos temas y
los tamaños 1440×900, 1600×1000, 1920×1080 y 2048×1320.
El estado real del piloto se registra en [review.md](review.md).
No interpretar un resultado skipped como una prueba aprobada.

## Licencia y reversión

El HTML incorpora código del visor Archify. Se conserva su licencia MIT en
[ARCHIFY-LICENSE.txt](ARCHIFY-LICENSE.txt). No se incorporan logotipos al modelo.
Archify no se copia completo al repositorio: solo modelo, HTML, recibo,
documentación y script de generación.

Para retirar el piloto basta revertir el PR de documentación en Git.
No hay recursos de OpenShift ni servicios publicados que desinstalar.
