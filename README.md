# Kong Community DB-less sobre OpenShift CRC

Laboratorio reproducible para instalar Kong Gateway Community en modo DB-less sobre OpenShift Local (CRC), publicar el proxy mediante una Route HTTPS, exponer aplicaciones mediante Kong Ingress Controller y validar plugins Community con OpenShift Pipelines/Tekton.

## Estado validado

| Componente | Versión/valor |
|---|---|
| OpenShift Local | CRC 4.22.1 |
| Helm chart | `kong-3.4.1` |
| Kong Gateway | `3.9.3` |
| Kong Ingress Controller | `3.5` |
| Persistencia | DB-less (`database=off`) |
| Namespace de Kong | `kong` |
| Namespace de aplicaciones | `kong-demo` |

## Arquitectura

```text
Cliente HTTPS
  -> Route kong-proxy (OpenShift)
  -> Service kong-kong-proxy
  -> Kong Gateway
     -> /demo  -> Service kong-echo   -> Pod app 1
     -> /demo2 -> Service kong-echo-2 -> Pod app 2
     -> /transform -> Service kong-transform-echo -> Pod de observación
```

Las aplicaciones no se conectan activamente con Kong. Kong Ingress Controller observa los recursos `Ingress` cuya clase es `kong`, configura el gateway y reenvía cada solicitud al `Service` declarado como backend.

## Estructura

```text
.
├── docs/
├── helm/kong/values-db-less.yaml
├── manifests/
│   ├── namespaces/
│   ├── kong/
│   ├── apps/
│   └── plugins/
├── pipelines/
│   ├── rbac/
│   ├── pipelines/
│   └── runs/
├── scripts/
│   ├── powershell/
│   └── bash/
└── tests/
```

## Instalación rápida

PowerShell:

```powershell
.\scripts\powershell\install-kong.ps1
.\scripts\powershell\deploy-demo-apps.ps1
.\scripts\powershell\validate-lab.ps1
```

Linux/Bash:

```bash
./scripts/bash/install-kong.sh
./scripts/bash/deploy-demo-apps.sh
./scripts/bash/validate-lab.sh
```

## Pruebas

```text
https://kong-proxy-kong.apps-crc.testing/demo
https://kong-proxy-kong.apps-crc.testing/demo2
```

Respuestas esperadas:

```text
Respuesta recibida a traves de Kong Community
Segunda aplicacion publicada a traves de Kong Community
```

## Laboratorio automatizado de plugins

Cada prueba sigue el mismo ciclo controlado:

```text
validar estado inicial -> crear PipelineRun -> aplicar plugin
-> comprobar comportamiento -> verificar rutas de control -> documentar
-> desasociar plugin -> eliminar CR -> confirmar rollback
```

| Plugin | Ruta | Validación principal | Estado |
|---|---|---|---|
| `rate-limiting` | `/demo` | 5 solicitudes permitidas y siguientes en 429 | Aprobado y revertido |
| `correlation-id` | `/demo` | UUID generado y valor del cliente preservado | Aprobado y revertido |
| `request-transformer` | `/transform` | Header agregado antes del upstream | Aprobado y revertido |
| `response-transformer` | `/transform` | Header agregado a la respuesta | Aprobado y revertido |
| `cors` | `/transform` | Preflight, origen permitido y origen no autorizado | Aprobado y revertido |
| `request-size-limiting` | `/transform` | 512 bytes en 200 y 2048 bytes en 413 | Aprobado y revertido |
| `request-termination` | `/transform` | Terminación en Kong con HTTP 503 | Aprobado y revertido |
| `ip-restriction` | `/transform` | Denegación 403 y permiso 200 por CIDR | Aprobado y revertido |
| `key-auth` | `/transform` | Sin key 401, key inválida 401 y válida 200 | Aprobado y revertido |

Las Pipelines usan `/demo` y `/demo2` como rutas de control para demostrar que
el plugin solamente afecta el Ingress objetivo. Los resultados reales quedan
en `docs/plugin-test-results/` y las guías detalladas en `docs/plugin-tests/`.

### Requisitos para ejecutar Pipelines

```powershell
oc apply -k .\pipelines\rbac --dry-run=server
oc apply -k .\pipelines\rbac
oc get serviceaccount,role,rolebinding -n kong-demo
```

`--dry-run=server` pide al API Server que valide los objetos sin persistirlos.
El segundo comando crea o actualiza el ServiceAccount y su RBAC namespace-scoped.

## Documentación

- [Arquitectura](docs/architecture.md)
- [Instalación](docs/installation.md)
- [Validación](docs/validation.md)
- [Operación](docs/operations.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Compatibilidad y plan de pruebas de plugins](docs/plugins-compatibility-test-plan.md)
- [Pruebas automatizadas con OpenShift Pipelines](docs/openshift-pipelines.md)
- [Rate Limiting](docs/plugin-tests/rate-limiting.md)
- [Correlation ID](docs/plugin-tests/correlation-id.md)
- [Request/Response Transformers](docs/plugin-tests/transformers.md)
- [CORS](docs/plugin-tests/cors.md)
- [Request Size Limiting](docs/plugin-tests/request-size-limiting.md)
- [Request Termination](docs/plugin-tests/request-termination.md)
- [IP Restriction](docs/plugin-tests/ip-restriction.md)
- [Key Authentication](docs/plugin-tests/key-auth.md)
- [Desinstalación](docs/uninstall.md)

## Seguridad

- No se despliega PostgreSQL.
- Admin API, Kong Manager, Portal y Portal API permanecen sin exposición externa.
- El proxy se publica mediante una única Route HTTPS de OpenShift.
- OpenShift aplica la SCC `restricted-v2` a las aplicaciones de prueba.
