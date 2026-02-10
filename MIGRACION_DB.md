# Proceso de Migración de Base de Datos (QA -> Producción)

Este documento detalla los pasos para **respaldar**, limpiar y transferir la base de datos desde QA hacia Producción en Google Cloud Platform.

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

1. **Eliminar la base de datos actual**:
```bash
gcloud sql databases delete tickethome --instance=prod-ticket-home
```

2. **Crear una base de datos nueva y limpia**:
```bash
gcloud sql databases create tickethome --instance=prod-ticket-home --charset=UTF8 --collation=en_US.UTF8
```

## 6. Importar Nuevo Respaldo (PROD)
Finalmente, importamos los datos nuevos sobre la base de datos limpia.
```bash
gcloud sql import sql prod-ticket-home gs://prod-ticket-home-backup/dump-transfer-qa-tickethome.sql --database=tickethome
```
