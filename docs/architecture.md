# Arquitectura

## Flujo de red

```text
Cliente HTTPS
  -> Router de OpenShift
  -> Route kong/kong-proxy (TLS edge)
  -> Service kong/kong-kong-proxy:80
  -> Kong Gateway:8000
  -> configuración generada por Kong Ingress Controller
  -> Service de la aplicación:5678
  -> Pod http-echo:5678
```

## Responsabilidad de cada recurso

| Recurso | Responsabilidad |
|---|---|
| Deployment | Mantiene los pods de una aplicación. |
| Service | Proporciona un destino estable y selecciona pods mediante labels. |
| Ingress | Relaciona un path externo con un Service backend. |
| IngressClass `kong` | Asigna el Ingress a Kong Ingress Controller. |
| Route `kong-proxy` | Publica el proxy de Kong fuera de OpenShift. |

Cada aplicación tiene Deployment y Service propios. En este laboratorio también usa un Ingress independiente, aunque Kubernetes permite agrupar varios paths en un único Ingress.

No se crea una Route por aplicación: todas reutilizan la Route del proxy y Kong decide el backend según el path.

## DB-less

`env.database=off` evita la dependencia de PostgreSQL. Kong Ingress Controller observa la API de Kubernetes y aplica la configuración al Gateway. La Admin API no se publica externamente.

