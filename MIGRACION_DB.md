# Proceso de Migración de Base de Datos (QA -> Producción)

Este documento detalla los pasos para **respaldar**, limpiar y transferir la base de datos desde QA hacia Producción en Google Cloud Platform.

## Notas Importantes (Contexto)
*   **Instancia vs Base de Datos**: Cuando hablamos de "eliminar" en el paso 5, nos referimos a la **base de datos lógica** (`tickethome`), NUNCA a la **instancia** de Cloud SQL (`prod-ticket-home`). La instancia debe permanecer activa.
*   **Usuarios de BD**: QA utiliza `tickethome_user` y PROD utiliza `tickethome-app`. El dump de QA puede traer referencias al usuario de origen, pero esto no ha causado bloqueos críticos en la importación.
*   **Automatización**: Se recomienda usar el flag `--quiet` en los comandos de borrado e importación para evitar prompts interactivos.

## 0. **Seguridad (CRÍTICO)**: Respaldo de Producción
Antes de tocar nada, generamos un **respaldo de seguridad (snapshot)** de la base de datos de producción actual.

```bash
gcloud config set project prod-ticket-home-redsalud
gcloud sql export sql prod-ticket-home gs://prod-ticket-home-backup/respaldo-previo-prod-tickethome.sql --database=tickethome --offload
```

## 1. Configurar Proyecto Origen (QA)
Nos aseguramos de estar en el proyecto de QA.
```bash
gcloud config set project qa-ticket-home-redsalud
```

## 2. Exportar Base de Datos (QA)
Exportamos la base de datos de QA `tickethome` al bucket de QA.
```bash
gcloud sql export sql qa-ticket-home gs://qa-ticket-home-backup-transport/dump-qa-tickethome.sql --database=tickethome --offload
```

## 3. Transferir Archivo a Producción
Transferimos el respaldo de QA al bucket de Producción.
```bash
gsutil cp gs://qa-ticket-home-backup-transport/dump-qa-tickethome.sql gs://prod-ticket-home-backup/dump-transfer-qa-tickethome.sql
```

## 4. Configurar Proyecto Destino (PROD)
Cambiamos al proyecto de Producción.
```bash
gcloud config set project prod-ticket-home-redsalud
```

## 5. Limpieza y Recreación (PROD)
Para evitar conflictos durante la importación, **recreamos la base de datos lógica** `tickethome` para asegurarnos que esté **totalmente vacía**.

1. **Eliminar la base de datos actual** (No la instancia):
```bash
gcloud sql databases delete tickethome --instance=prod-ticket-home --quiet
```

2. **Crear una base de datos nueva y limpia**:
```bash
gcloud sql databases create tickethome --instance=prod-ticket-home --charset=UTF8 --collation=en_US.UTF8
```

## 6. Importar Nuevo Respaldo (PROD)
Finalmente, importamos los datos nuevos sobre la base de datos limpia.
```bash
gcloud sql import sql prod-ticket-home gs://prod-ticket-home-backup/dump-transfer-qa-tickethome.sql --database=tickethome --quiet
```

## 7. Verificación (Opcional)
Si un comando parece tardar, puedes revisar el estado de la operación con:
```bash
gcloud sql operations list --instance=prod-ticket-home --limit=5
```
