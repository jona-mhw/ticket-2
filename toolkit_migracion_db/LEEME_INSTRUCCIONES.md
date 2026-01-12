# Resumen de Migración de Base de Datos: QA a PROD
**Proyecto:** Ticket-Home
**Fecha:** 12 de Enero de 2026

Este documento resume el proceso exitoso de migración de la base de datos de los entornos de QA a Producción, detallando los desafíos encontrados y las soluciones aplicadas.

---

## 🚀 Etapas de la Migración

1. **Preparación y Exportación (QA):**
   - Se creó un bucket de GCS en el proyecto de QA (`gs://qa-ticket-home-backup-transport`).
   - Se otorgaron permisos de `objectAdmin` a la cuenta de servicio de Cloud SQL de QA.
   - Se exportó la base de datos `tickethome` mediante `gcloud sql export sql`.

2. **Limpieza del Destino (PROD):**
   - Se identificó que la base de datos en PROD ya contenía tablas que causaban conflictos de esquema.
   - Se ejecutó un comando de limpieza profunda: 
     ```sql
     DROP SCHEMA public CASCADE;
     CREATE SCHEMA public;
     ```
   - *Nota:* Esto reseteó todos los permisos del esquema que debieron ser restaurados posteriormente.

3. **Traslado de Datos y Permisos:**
   - Se creó un bucket en el proyecto PROD (`gs://prod-ticket-home-backup`) para facilitar el acceso de la cuenta de servicio local.
   - Se transfirió el archivo `.sql` entre buckets usando `gsutil cp`.
   - Se otorgaron permisos de lectura (`objectViewer`) a la cuenta de servicio de Cloud SQL de PROD sobre el nuevo bucket.

4. **Importación (PROD):**
   - Se utilizó el comando nativo `gcloud sql import sql` (con el usuario `--user=postgres`) para procesar el archivo. Este método es superior a copiar/pegar en SQL Studio porque soporta la sintaxis `COPY FROM stdin`.

5. **Restauración de Permisos de Aplicación:**
   - Tras la limpieza del esquema, el usuario de la aplicación (`tickethome-app`) perdió privilegios.
   - Se aplicaron GRANTs para devolver el control al usuario de la app sobre tablas y secuencias.

---

## 🛠️ Soluciones a Problemas Comunes

### 1. Error de "Invalid Schema Name" o "Insufficient Privilege"
**Causa:** Al recrear el esquema `public`, los permisos por defecto no incluyen al usuario de la aplicación.
**Solución:**
```sql
GRANT ALL ON SCHEMA public TO "tickethome-app";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "tickethome-app";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "tickethome-app";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "tickethome-app";
```

### 2. Error de Sintaxis en Cloud SQL Studio (`\restrict` o `COPY`)
**Causa:** Cloud SQL Studio es un cliente web limitado y no procesa comandos de metacontrol de `pg_dump` ni el formato `FROM stdin`.
**Solución:** No usar SQL Studio para importaciones masivas. Usar siempre `gcloud sql import sql` apuntando a un archivo en un bucket de GCS.

### 3. Conexiones Activas Bloqueando el Drop
**Causa:** Cloud Run mantiene conexiones abiertas a la BD.
**Solución:** Escalar temporalmente Cloud Run a 0 instancias:
```bash
gcloud run services update [SERVICE] --min-instances=0 --max-instances=1 --region=[REGION]
```

---

## 📝 Consideraciones para Futuras Instancias

- **Nombre de BD:** Confirmar siempre el nombre interno (en este caso era `tickethome` y no `ticket_home`).
- **Nombres de Servicio:** El servicio de Cloud Run en prod se denomina `ticket-home-prod`.
- **Propagación de IAM:** Los permisos de Google Cloud Storage (IAM) pueden tardar hasta 1-2 minutos en ser efectivos para la cuenta de servicio de SQL. Siempre esperar un momento después del `gsutil iam ch`.
- **Dueño de Objetos:** Al importar como `postgres`, las tablas pertenecen a `postgres`. Siempre recordar ejecutar los `GRANT` finales para que el usuario `tickethome-app` pueda operar normalmente.

---
**Resultado Final:** Aplicación operativa en [ticket-home-prod](https://ticket-home-prod-blvyogx66a-tl.a.run.app) con datos sincronizados.
