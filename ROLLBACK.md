# Guía de Recuperación (Rollback) - Ticket Home

Este documento detalla cómo volver a la versión estable anterior en caso de problemas con el despliegue de la nueva versión.

## Versión de Respaldo

La versión estable identificada antes del despliegue del 11/02/2026 es:
**Revisión:** `ticket-home-00022-ss5`

## Procedimiento de Rollback

Si detectas errores críticos después del despliegue, ejecuta el siguiente comando en tu terminal para redirigir el 100% del tráfico a la revisión anterior de inmediato:

```powershell
gcloud run services update-traffic ticket-home --region=southamerica-west1 --to-revisions=ticket-home-00022-ss5=100
```

### Verificación

Después de ejecutar el comando, verifica que el tráfico se haya movido correctamente:

```powershell
gcloud run services describe ticket-home --region=southamerica-west1 --format="value(status.traffic)"
```

Deberías ver que `ticket-home-00022-ss5` tiene el 100% del tráfico.
