# FIX: IAP Authentication - "Acceso No Autorizado" en QA

**Fecha**: 2025-11-25  
**Autor**: Jonathan Segura (con asistencia de Gemini)  
**Revisión**: ticket-home-00042-2p2

---

## Problema Original

Al intentar acceder a https://qa-ticket-home.mhwdev.dev se mostraba el error:

```
Acceso No Autorizado
Has sido autenticado correctamente a través de tu cuenta de Google,
pero no tienes permiso para acceder a esta aplicación.

Tu cuenta de Google (jonathan.segura@redsalud.cl) no está registrada 
en nuestra base de datos.
```

---

## Análisis del Problema

### ✅ Qué estaba funcionando:
1. Google IAP autenticaba correctamente al usuario
2. El usuario estaba en el grupo correcto: `qa-ticket-home-rs@googlegroups.com`
3. Los secrets en Secret Manager estaban configurados correctamente

### ❌ Qué NO estaba funcionando:

**Problema 1: Variables de entorno faltantes para validación JWT**
- La aplicación Flask requería `GCP_PROJECT_NUMBER` y `BACKEND_SERVICE_ID` para validar el JWT de IAP
- Sin estas variables, la app rechazaba con 403 incluso después de pasar IAP
- Error en logs: `CRITICAL: IAP mal configurado. Faltan GCP_PROJECT_NUMBER o BACKEND_SERVICE_ID`

**Problema 2: Superusuarios nunca sincronizados a la base de datos**
- `RESET_DB_ON_STARTUP=false` en el último deployment
- Los superusuarios definidos en Secret Manager nunca se sincronizaron a la tabla `Superuser` en PostgreSQL
- La lógica de autenticación busca el email en la tabla `Superuser` para crear usuarios automáticamente
- Como la tabla estaba vacía, ningún superusuario podía acceder

**Problema 3: Variable ENVIRONMENT incorrecta**
- `ENVIRONMENT` estaba configurado como "production" en vez de "qa"
- Esto causaba logs confusos y comportamiento no esperado

---

## Por Qué Nos Costó Tanto

### 1. **Confusión inicial sobre la causa**
   - Pensamos que era CSRF o permisos de Terraform
   - El error apuntaba a "no registrado en BD" pero no era obvio que los superusers nunca se habían sincronizado

### 2. **Problemas con Terraform**
   - Intentamos arreglar via Terraform pero teníamos errores de permisos IAM
   - El archivo `main.tf` se corrompió múltiples veces al intentar editarlo programáticamente
   - Perdimos tiempo intentando solucionar permisos en vez de ir directo a gcloud

### 3. **Secrets vs Variables de Entorno**
   - Confundimos secrets (DATABASE_URL, SECRET_KEY) con variables de entorno normales
   - Al intentar actualizar con `--set-secrets` sobrescribimos y borramos accidentalmente DATABASE_URL
   - Tuvimos que restaurar la configuración completa

### 4. **Falta de logs de startup**
   - Como RESET_DB_ON_STARTUP=false, no había logs de sincronización de superusers
   - Esto hizo difícil diagnosticar que los superusers simplemente no existían en la BD

---

## Solución Implementada

### Paso 1: Actualizar Secret Manager
```bash
echo "global_admin@tickethome.com;jonathan.segura@redsalud.cl;admin@tickethome.com" | \
  gcloud secrets versions add superuser-emails --data-file=-
```

### Paso 2: Deployment con gcloud (bypass de Terraform)
```bash
gcloud run services update ticket-home \
  --region=southamerica-west1 \
  --project=qa-ticket-home-redsalud \
  --update-env-vars="GCP_PROJECT_NUMBER=85153475663,BACKEND_SERVICE_ID=2148322621403404401,RESET_DB_ON_STARTUP=true,ENVIRONMENT=qa"
```

**Resultado**: Revisión `ticket-home-00042-2p2` desplegada exitosamente

### Paso 3: Verificación
- Container arrancó correctamente
- Ejecutó `flask reset-db-qa-minimal` 
- Sincronizó los 3 superusuarios a la tabla `Superuser`
- Usuario `jonathan.segura@redsalud.cl` pudo acceder ✅

---

## Variables de Entorno Configuradas

```
FLASK_ENV=production
FLASK_DEBUG=false
ENABLE_IAP=true
ENVIRONMENT=qa                          ← CORREGIDO
ENABLE_DEMO_LOGIN=false
RESET_DB_ON_STARTUP=true                ← ACTIVADO temporalmente
USE_QA_MINIMAL_SEED=true
GCP_PROJECT_NUMBER=85153475663          ← AGREGADO
BACKEND_SERVICE_ID=2148322621403404401  ← AGREGADO

# Secrets (desde Secret Manager)
DATABASE_URL=tickethome-db-url:latest
SECRET_KEY=tickethome-secret-key:latest
SUPERUSER_EMAILS=superuser-emails:latest
```

---

## Lecciones Aprendidas

1. **Usar gcloud directamente es más confiable que Terraform** para cambios rápidos en Cloud Run
2. **Verificar SIEMPRE los logs de startup** para confirmar que los comandos de inicialización se ejecutaron
3. **Diferenciar entre secrets y env vars**: 
   - Secrets: `--update-secrets` (para DATABASE_URL, etc.)
   - Variables: `--update-env-vars` (para GCP_PROJECT_NUMBER, etc.)
4. **Estado de la BD importa**: Si `RESET_DB_ON_STARTUP=false`, la data anterior persiste
5. **Principio KISS**: Cuando algo no funciona, ir por la solución más directa (gcloud) en vez de complicar con Terraform

---

## Archivos Modificados

- ✅ **Secret Manager**: `superuser-emails` (nueva versión 10)
- ✅ **Cloud Run Service**: `ticket-home` (revisión 00042-2p2)
- ❌ **Terraform**: NO modificado (se evitó por complejidad)

---

## Para Futuros Deployments

Ver archivo: `20251125-how-to-deploy.txt`

**TL;DR**: Usar gcloud, no Terraform, para deployments de QA.

---

## Referencias

- IAP Documentation: https://cloud.google.com/iap/docs
- Cloud Run Env Vars: https://cloud.google.com/run/docs/configuring/environment-variables
- Secret Manager: https://cloud.google.com/secret-manager/docs

---

**Estado Final**: ✅ RESUELTO  
**Acceso QA**: https://qa-ticket-home.mhwdev.dev  
**Email autorizado**: jonathan.segura@redsalud.cl
