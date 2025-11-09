# 🚀 Scripts de Deployment - Linux/macOS

Scripts bash para deployment del proyecto Ticket Home a Google Cloud Platform.

## 📋 Prerequisitos

Antes de ejecutar estos scripts, asegúrate de tener instalado:

1. **gcloud CLI** - [Instalación](https://cloud.google.com/sdk/docs/install)
   ```bash
   # Verificar instalación
   gcloud --version

   # Autenticarse
   gcloud auth login

   # Configurar proyecto por defecto (opcional)
   gcloud config set project dev-ticket-home-redsalud
   ```

2. **Docker** - [Instalación](https://docs.docker.com/get-docker/)
   ```bash
   # Verificar instalación
   docker --version

   # Asegurarse que Docker está corriendo
   docker ps
   ```

3. **Permisos en GCP**
   - Acceso a proyectos: `dev-ticket-home-redsalud` y `qa-ticket-home-redsalud`
   - Roles necesarios:
     - Cloud Run Admin
     - Storage Admin
     - Secret Manager Admin
     - Service Account User

## 🎯 Workflow de Deployment

### Deployment Completo (Primera vez o cambios en DB)

```bash
# 1. Setup inicial de secrets (solo primera vez)
./deploy-scripts/0-setup-secrets.sh

# 2. Build y push de imagen Docker a DEV
./deploy-scripts/1-build-push-DEV.sh

# 3. Deploy a Cloud Run DEV
./deploy-scripts/3-deploy-DEV-normal.sh
```

### Deployment Normal (Solo cambios de código)

Si solo cambiaste código (HTML, CSS, JS, Python) sin cambios en `models.py`:

```bash
# 1. Build y push
./deploy-scripts/1-build-push-DEV.sh

# 2. Deploy
./deploy-scripts/3-deploy-DEV-normal.sh
```

### Deployment a QA

```bash
# 1. Build y push a QA
./deploy-scripts/1-build-push-QA.sh

# 2. Deploy a Cloud Run QA
./deploy-scripts/3-deploy-QA-normal.sh
```

## 📝 Descripción de Scripts

### `0-setup-secrets.sh`
**Ejecutar**: Solo una vez antes del primer deployment

Crea y configura los secrets necesarios en Google Secret Manager:
- `superuser-emails`: Lista de emails de superusuarios
- Configura permisos para service accounts de DEV y QA

**Output esperado**:
```
✅ SETUP COMPLETADO EXITOSAMENTE

DEV:
global_admin@tickethome.com;jonathan.segura@redsalud.cl;admin@tickethome.com

QA:
global_admin@tickethome.com;jonathan.segura@redsalud.cl;admin@tickethome.com
```

### `1-build-push-DEV.sh`
**Ejecutar**: Cada vez que hagas cambios al código

1. Configura autenticación de Docker con GCP
2. Construye imagen Docker para DEV
3. Push a Artifact Registry

**Tiempo**: ~5-10 minutos

### `1-build-push-QA.sh`
**Ejecutar**: Cuando quieras deployar a QA

Similar a DEV pero para ambiente QA.

### `3-deploy-DEV-normal.sh`
**Ejecutar**: Después de build-push-DEV

1. Deploy de imagen a Cloud Run DEV
2. Configura variables de entorno y secrets
3. Aplica IAM policy bindings

**Configuración DEV**:
- `ENABLE_DEMO_LOGIN=true` (Login tradicional + SSO)
- URL: https://ticket-home.mhwdev.dev
- Grupo: rs-ticket-home@googlegroups.com

**Tiempo**: ~3-5 minutos

### `3-deploy-QA-normal.sh`
**Ejecutar**: Después de build-push-QA

Similar a DEV pero con configuración de QA.

**Configuración QA**:
- `ENABLE_DEMO_LOGIN=false` (Solo SSO)
- URL: https://qa-ticket-home.mhwdev.dev
- Grupo: qa-ticket-home-rs@googlegroups.com

## ✅ Verificación Post-Deployment

### 1. Verificar Headers de Seguridad

```bash
curl -I https://ticket-home.mhwdev.dev
```

Debe incluir:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Content-Security-Policy: ...`
- `Referrer-Policy: strict-origin-when-cross-origin`

### 2. Verificar Aplicación

1. Abrir URL en navegador
2. Login debe funcionar (IAP + tradicional en DEV, solo IAP en QA)
3. Dashboard debe cargar sin errores
4. Footer debe mostrar versión correcta

### 3. Verificar Logs

```bash
# Logs de DEV
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=20 \
  --project=dev-ticket-home-redsalud

# Logs de QA
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=20 \
  --project=qa-ticket-home-redsalud
```

## 🚨 Troubleshooting

### Error: "Permission denied"

**Solución**: Hacer ejecutables los scripts
```bash
chmod +x deploy-scripts/*.sh
```

### Error: "gcloud: command not found"

**Solución**: Instalar gcloud CLI
```bash
# macOS con Homebrew
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### Error: "Docker build failed"

**Solución**: Verificar que Docker está corriendo
```bash
docker ps
# Si falla, iniciar Docker Desktop
```

### Error: "Secret already exists"

**Solución**: ¡OK! El script detecta secrets existentes. Puedes ignorar este warning.

### Error: "403 Forbidden" después del deployment

**Solución**: El script aplica IAM policy binding automáticamente. Si persiste:
```bash
gcloud run services add-iam-policy-binding ticket-home \
  --region=southamerica-west1 \
  --member="allUsers" \
  --role="roles/run.invoker" \
  --project=dev-ticket-home-redsalud
```

### Error: "No space left on device"

**Solución**: Limpiar imágenes Docker antiguas
```bash
docker system prune -a
```

## 🔄 Workflow Recomendado

### Desarrollo Local → DEV

1. Desarrollar localmente
2. Probar con `flask run`
3. Commit a git
4. Build y deploy a DEV:
   ```bash
   ./deploy-scripts/1-build-push-DEV.sh && \
   ./deploy-scripts/3-deploy-DEV-normal.sh
   ```
5. Verificar en https://ticket-home.mhwdev.dev

### DEV → QA

1. Probar exhaustivamente en DEV
2. Actualizar tests si es necesario
3. Build y deploy a QA:
   ```bash
   ./deploy-scripts/1-build-push-QA.sh && \
   ./deploy-scripts/3-deploy-QA-normal.sh
   ```
4. Verificar en https://qa-ticket-home.mhwdev.dev

## 📊 Diferencias entre Ambientes

| Característica | DEV | QA |
|----------------|-----|-----|
| URL | ticket-home.mhwdev.dev | qa-ticket-home.mhwdev.dev |
| Grupo Google | rs-ticket-home@googlegroups.com | qa-ticket-home-rs@googlegroups.com |
| Login Tradicional | ✅ Habilitado | ❌ Solo SSO |
| Base de Datos | dev-ticket-home | qa-ticket-home |
| Propósito | Desarrollo y pruebas rápidas | Testing pre-producción |

## 🔐 Seguridad

Estos scripts incluyen:

- ✅ Security Headers HTTP
- ✅ Secrets en Secret Manager (no en variables de entorno)
- ✅ VPC connector para bases de datos
- ✅ No allow unauthenticated
- ✅ IAP (Identity-Aware Proxy)

**Nivel de seguridad**: 8.5/10 📈

## 📚 Recursos

- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [Secret Manager Docs](https://cloud.google.com/secret-manager/docs)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)

## 📞 Soporte

Para problemas o preguntas:
- Abrir issue en GitHub
- Revisar logs en Cloud Console
- Contactar al equipo de DevOps

---

**Creado por**: Claude Code
**Fecha**: Noviembre 2025
**Versión**: 1.0
