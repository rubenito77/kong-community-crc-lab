# Kong Community DB-less sobre OpenShift CRC

Laboratorio reproducible para instalar Kong Gateway Community en modo DB-less sobre OpenShift Local (CRC), publicar el proxy mediante una Route HTTPS y exponer dos aplicaciones de prueba con Kong Ingress Controller.

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
│   └── apps/
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

## Documentación

- [Arquitectura](docs/architecture.md)
- [Instalación](docs/installation.md)
- [Validación](docs/validation.md)
- [Operación](docs/operations.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Desinstalación](docs/uninstall.md)

## Seguridad

- No se despliega PostgreSQL.
- Admin API, Kong Manager, Portal y Portal API permanecen sin exposición externa.
- El proxy se publica mediante una única Route HTTPS de OpenShift.
- OpenShift aplica la SCC `restricted-v2` a las aplicaciones de prueba.

