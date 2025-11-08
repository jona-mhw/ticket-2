# Archivos de Configuración de Infraestructura

Esta carpeta contiene configuraciones exportadas de recursos GCP.

## Archivos

### Load Balancer Configuration
- `url-map-backup.yaml` - Backup del URL map original
- `url-map-updated.yaml` - URL map actualizado con path matcher para /static/*

## Uso

Estos archivos son útiles para:
- Backup de configuraciones
- Replicar configuración en otros ambientes
- Versionado de cambios de infraestructura

## Aplicar Configuraciones

```bash
# Importar URL map
gcloud compute url-maps import [NAME] \
  --source=url-map-updated.yaml \
  --global \
  --project=[PROJECT_ID]
```

## Exportar Nuevas Configuraciones

```bash
# Exportar URL map actual
gcloud compute url-maps export [NAME] \
  --destination=url-map-backup.yaml \
  --global \
  --project=[PROJECT_ID]
```
