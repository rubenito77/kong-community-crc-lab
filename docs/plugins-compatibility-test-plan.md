# Compatibilidad y plan de pruebas de plugins

## 1. Alcance validado

Este documento aplica al laboratorio:

- Kong Gateway Community `3.9.x` (imagen `kong:3.9`).
- Kong Ingress Controller `3.5`.
- Helm chart `kong-3.4.1`.
- OpenShift Local CRC 4.22.1.
- Modo DB-less, administrado mediante recursos Kubernetes.

La validación usa dos criterios diferentes:

1. **Incluido en Community 3.9:** el plugin aparece en `BUNDLED_PLUGINS` del código oficial de Kong 3.9.
2. **Compatible con DB-less:** la documentación oficial declara la topología `db-less` como soportada.

Un plugin Enterprise puede admitir técnicamente DB-less, pero eso no significa que esté disponible en la imagen Community. Por este motivo, la matriz de pruebas solo acepta como ejecutables sin licencia los plugins incluidos en `BUNDLED_PLUGINS`.

## 2. Plugins incluidos en Kong Community 3.9

El código oficial de Kong 3.9.0 y 3.9.1 declara los siguientes plugins incluidos:

| Categoría | Plugins incluidos |
|---|---|
| Autenticación y autorización | `jwt`, `acl`, `oauth2`, `key-auth`, `hmac-auth`, `basic-auth`, `ldap-auth`, `session` |
| Seguridad | `ip-restriction`, `bot-detection`, `cors`, `request-size-limiting`, `request-termination`, `standard-webhooks` |
| Control de tráfico | `rate-limiting`, `response-ratelimiting`, `proxy-cache`, `redirect` |
| Transformación | `request-transformer`, `response-transformer`, `pre-function`, `post-function` |
| Observabilidad y logging | `correlation-id`, `prometheus`, `opentelemetry`, `zipkin`, `statsd`, `datadog`, `file-log`, `http-log`, `tcp-log`, `udp-log`, `syslog`, `loggly` |
| Integraciones | `aws-lambda`, `azure-functions` |
| Protocolos | `grpc-gateway`, `grpc-web`, `acme` |
| IA incluidos en 3.9 | `ai-proxy`, `ai-prompt-decorator`, `ai-prompt-template`, `ai-prompt-guard`, `ai-request-transformer`, `ai-response-transformer` |

Fuente primaria: [`kong/constants.lua` de Kong 3.9.1](https://github.com/Kong/kong/blob/3.9.1/kong/constants.lua).

## 3. Plugins que no se deben confundir con Community

Los siguientes ejemplos aparecen en el Plugin Hub pero requieren Kong Enterprise/licencia y quedan fuera del laboratorio Community:

| Plugin | Motivo de exclusión |
|---|---|
| `openid-connect` | Enterprise only. |
| `rate-limiting-advanced` | Enterprise only; no confundir con `rate-limiting`. |
| `service-protection` | Enterprise only. |
| `mtls-auth` | Enterprise only. |
| `oauth2-introspection` | Enterprise only. |
| `jwt-signer` | Enterprise only; no confundir con `jwt`. |
| `key-auth-enc` | Enterprise only; no confundir con `key-auth`. |
| `ldap-auth-advanced` | Enterprise only; no confundir con `ldap-auth`. |
| `request-validator` | Enterprise only. |
| `graphql-rate-limiting-advanced` | Enterprise only. |
| `ai-rate-limiting-advanced` | Requiere AI Gateway Enterprise. |

La lista no pretende enumerar todos los productos Enterprise: documenta las confusiones más probables para este laboratorio.

## 4. Modelo de configuración en Kubernetes

Cada prueba seguirá este patrón:

```text
KongPlugin (configuración)
       +
anotación konghq.com/plugins
       ↓
Ingress / Service / KongConsumer
       ↓
Kong Ingress Controller
       ↓
Kong Gateway DB-less
```

Ejemplo de asociación a una ruta:

```yaml
metadata:
  annotations:
    konghq.com/plugins: nombre-del-plugin
```

Los plugins se aplicarán inicialmente a `/demo` y `/demo2` de forma granular. No se utilizarán plugins globales hasta comprobar que el comportamiento local es correcto.

## 5. Reglas del plan de pruebas

- Ejecutar una familia de plugins por vez.
- Registrar estado antes y después de cada cambio.
- Probar un caso permitido y un caso rechazado.
- Verificar respuesta, headers y logs de Kong.
- Confirmar que la otra aplicación continúa funcionando.
- Conservar manifiestos y scripts en Git.
- Incluir un procedimiento de rollback para cada prueba.
- No exponer la Admin API.
- No almacenar credenciales reales en Git.
- Usar Secrets de Kubernetes para API keys, contraseñas y material criptográfico.

## 6. Fases de implementación

### Fase 0 - Inventario y línea base

| ID | Prueba | Resultado esperado |
|---|---|---|
| P00-01 | Consultar plugins cargados dentro del pod Kong | La lista contiene los plugins Community requeridos. |
| P00-02 | Probar `/demo` y `/demo2` sin plugins | Ambas rutas responden HTTP 200. |
| P00-03 | Revisar logs del controller | No existen errores de reconciliación. |
| P00-04 | Guardar manifiestos actuales | Existe rollback reproducible. |

### Fase 1 - Control de tráfico y protección básica

| ID | Plugin | Prueba positiva | Prueba negativa | Resultado esperado |
|---|---|---|---|---|
| P01-01 | `rate-limiting` | Realizar solicitudes dentro del límite | Superar el límite configurado | **Aprobada 2026-08-24:** HTTP 200 dentro del límite y HTTP 429 al excederlo. [Evidencia](plugin-test-results/rate-limiting-2026-08-24.md). |
| P01-02 | `request-size-limiting` | Enviar payload permitido | Enviar payload superior al máximo | **Aprobada 2026-08-26:** 512 bytes devolvieron HTTP 200 y 2048 bytes HTTP 413; rutas de control aisladas. [Evidencia](plugin-test-results/request-size-limiting-2026-08-26.md). |
| P01-03 | `request-termination` | Verificar ruta sin plugin | Activar terminación temporal | La ruta seleccionada devuelve el status configurado sin llegar al backend. |
| P01-04 | `ip-restriction` | Solicitar desde IP permitida | Solicitar desde IP denegada | Acceso permitido/HTTP 403 según lista. |

Para `rate-limiting` en este CRC con una sola réplica se usará `policy: local`. Si Kong escala a varias réplicas, los contadores locales divergen; para límites compartidos en DB-less debe evaluarse Redis.

### Fase 2 - Headers, CORS y transformaciones

| ID | Plugin | Prueba | Evidencia esperada |
|---|---|---|---|
| P02-01 | `correlation-id` | Solicitar `/demo` sin ID y con ID proporcionado por el cliente | **Aprobada 2026-08-25:** UUID generado, ID del cliente preservado y `/demo2` aislado. [Evidencia](plugin-test-results/correlation-id-2026-08-25.md). |
| P02-02 | `request-transformer` | Agregar header antes del backend | **Aprobada 2026-08-25:** el backend recibió `X-Lab-Request-Transform: added-by-kong`. [Evidencia](plugin-test-results/transformers-2026-08-25.md). |
| P02-03 | `response-transformer` | Agregar header de respuesta | **Aprobada 2026-08-25:** el cliente recibió `X-Lab-Response-Transform: added-by-kong`; rutas de control aisladas. [Evidencia](plugin-test-results/transformers-2026-08-25.md). |
| P02-04 | `cors` | Enviar preflight `OPTIONS` permitido | **Aprobada 2026-08-25:** HTTP 200 con origen, métodos, headers y max-age correctos. [Evidencia](plugin-test-results/cors-2026-08-25.md). |
| P02-05 | `cors` | Usar origen no autorizado | **Aprobada 2026-08-25:** el origen no fue reflejado ni recibió wildcard; `/demo` y `/demo2` quedaron aislados. [Evidencia](plugin-test-results/cors-2026-08-25.md). |

### Fase 3 - Autenticación y consumidores

| ID | Plugin | Prueba positiva | Prueba negativa | Resultado esperado |
|---|---|---|---|---|
| P03-01 | `key-auth` | API key válida | Sin key y key inválida | HTTP 200 con key válida; HTTP 401 en los otros casos. |
| P03-02 | `basic-auth` | Usuario/clave válidos | Credenciales inválidas | HTTP 200/401. |
| P03-03 | `jwt` | JWT HS256 válido | Token ausente, vencido o firma inválida | HTTP 200/401. |
| P03-04 | `acl` + autenticación | Consumer dentro del grupo | Consumer fuera del grupo | HTTP 200/403. |
| P03-05 | `hmac-auth` | Firma HMAC válida | Firma alterada o timestamp inválido | HTTP 200/401. |

Las credenciales se crearán como Secrets y no se publicarán valores sensibles en el repositorio.

### Fase 4 - Observabilidad

| ID | Plugin | Prueba | Evidencia esperada |
|---|---|---|---|
| P04-01 | `prometheus` | Generar tráfico y consultar métricas | Contadores y latencias de Kong visibles. |
| P04-02 | `http-log` | Enviar logs a un receptor HTTP temporal | El receptor obtiene el evento de acceso. |
| P04-03 | `opentelemetry` | Enviar spans a un collector OTLP | Traza con proxy latency y upstream latency. |
| P04-04 | `statsd` | Enviar métricas a receptor StatsD | Métricas recibidas con nombres esperados. |

`http-log`, `opentelemetry` y `statsd` requieren receptores adicionales. Se implementarán después de validar los plugins que no agregan dependencias.

### Fase 5 - Cache y comportamiento del proxy

| ID | Plugin | Prueba | Evidencia esperada |
|---|---|---|---|
| P05-01 | `proxy-cache` | Repetir solicitud cacheable | Header de cache cambia de `Miss` a `Hit`. |
| P05-02 | `redirect` | Solicitar path configurado | Respuesta de redirección y Location correctos. |
| P05-03 | `response-ratelimiting` | Backend devuelve header de cuota | Kong descuenta la cuota indicada. |

### Fase 6 - Seguridad adicional

| ID | Plugin | Prueba | Evidencia esperada |
|---|---|---|---|
| P06-01 | `bot-detection` | User-Agent normal y User-Agent bloqueado | Solicitud normal permitida y bot rechazado. |
| P06-02 | `standard-webhooks` | Webhook válido e inválido | Solo el webhook que cumple la especificación es aceptado. |
| P06-03 | `pre-function` / `post-function` | Función controlada de laboratorio | Modificación esperada sin errores Lua. |

Los plugins `pre-function` y `post-function` ejecutan código Lua y se probarán al final, con código mínimo revisado y solamente en el laboratorio.

## 7. Pruebas diferidas por dependencias

| Plugin | Dependencia o motivo |
|---|---|
| `oauth2` | Requiere diseño completo de consumidores, credenciales y flujo OAuth 2.0. |
| `ldap-auth` | Requiere servidor LDAP accesible. |
| `aws-lambda` | Requiere cuenta, función y credenciales AWS. |
| `azure-functions` | Requiere Function App y credenciales Azure. |
| `grpc-gateway`, `grpc-web` | Requieren backend gRPC de prueba. |
| `acme` | La Route actual termina TLS en OpenShift; necesita revisar el modelo TLS. |
| `zipkin` | Requiere collector Zipkin. |
| `datadog`, `loggly`, `syslog` | Requieren destinos externos. |
| Plugins de IA | Requieren proveedor/modelo, credenciales y validación de condiciones de uso. |

## 8. Evidencia que se guardará para cada prueba

Cada plugin tendrá una carpeta propia:

```text
plugins/<plugin>/
├── kongplugin.yaml
├── patch-ingress.yaml o patch-service.yaml
├── test.ps1
├── test.sh
├── rollback.ps1
├── rollback.sh
└── README.md
```

El README de cada prueba registrará:

- objetivo;
- alcance;
- prerrequisitos;
- recursos modificados;
- comandos PowerShell y Linux;
- resultado positivo;
- resultado negativo;
- headers y códigos HTTP esperados;
- comandos de diagnóstico;
- rollback;
- resultado real y fecha de ejecución.

## 9. Criterio de aprobación

Una prueba se considerará aprobada cuando:

1. Kong Ingress Controller acepte la configuración sin errores.
2. El caso positivo produzca el resultado esperado.
3. El caso negativo sea bloqueado o transformado según diseño.
4. `/demo2` siga respondiendo cuando la prueba solo afecta `/demo`.
5. El rollback restaure HTTP 200 sin recrear Kong.
6. No queden credenciales ni datos sensibles en Git.

## 10. Orden recomendado

El orden inicial será:

1. `rate-limiting`.
2. `correlation-id`.
3. `request-transformer` y `response-transformer`.
4. `cors`.
5. `request-size-limiting`.
6. `key-auth`.
7. `basic-auth`.
8. `jwt`.
9. `acl`.
10. `prometheus`.

Este orden comienza con plugins fáciles de observar y revertir, y deja consumidores, Secrets e integraciones externas para fases posteriores.

## 11. Fuentes oficiales

- [Plugins incluidos en Kong 3.9.1](https://github.com/Kong/kong/blob/3.9.1/kong/constants.lua)
- [Kong Plugin Hub](https://developer.konghq.com/plugins/)
- [Matriz de compatibilidad por topología](https://developer.konghq.com/plugins/compatibility/)
- [KongPlugin CRD](https://developer.konghq.com/kubernetes-ingress-controller/custom-resources/)
- [Anotación `konghq.com/plugins`](https://developer.konghq.com/kubernetes-ingress-controller/reference/annotations/)
- [Rate Limiting](https://developer.konghq.com/plugins/rate-limiting/)
- [Plugins personalizados](https://developer.konghq.com/kubernetes-ingress-controller/custom-plugins/)
