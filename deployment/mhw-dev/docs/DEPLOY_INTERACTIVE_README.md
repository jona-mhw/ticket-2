# 🚀 Deploy-Interactive.ps1 - Deployment Interactivo GCP

**Versión:** 1.0
**Fecha:** 2025-11-15
**Autor:** Claude
**Proyecto:** Ticket Home - RedSalud Chile

---

## 📋 Descripción

**Deploy-Interactive.ps1** es una herramienta PowerShell interactiva y visual que guía paso a paso en el proceso de deployment de Ticket Home a Google Cloud Platform.

El script proporciona:
- ✨ **Experiencia visual atractiva** con ASCII art y colores
- 🔐 **Validación automática** de credenciales GCP
- 📊 **Feedback en tiempo real** durante todo el proceso
- ⏸️ **Pausas interactivas** para revisar cada fase
- 🎨 **Pool de 50+ mensajes** entretenidos que rotan aleatoriamente
- 🔄 **Reintentos automáticos** en caso de errores

---

## ✅ Prerequisitos

### Software Necesario

1. **Windows 10/11** con PowerShell 5.1+ (o PowerShell Core 7+)
2. **gcloud CLI** instalado y configurado
   ```powershell
   # Verificar instalación
   gcloud --version
   ```
3. **Docker Desktop** instalado y corriendo
   ```powershell
   # Verificar instalación
   docker --version
   docker ps  # Debe mostrar containers sin error
   ```

### Permisos GCP

Tu cuenta de Google debe tener estos roles en el proyecto:
- Cloud Run Admin
- Compute Admin
- Cloud SQL Admin
- Secret Manager Admin
- Service Account Admin
- Security Admin (para IAP)

### Recursos GCP Previos

Antes de ejecutar el script, debes tener:
- ✅ Proyecto GCP creado
- ✅ Instancia Cloud SQL (PostgreSQL) corriendo
- ✅ Secrets en Secret Manager:
  - `mhw-database-url`
  - `mhw-secret-key`
  - `mhw-superuser-emails`
- ✅ Service Account creada con permisos
- ✅ Dominio disponible para configurar DNS

---

## 🚀 Uso del Script

### Método 1: Arrastrar y Soltar (Recomendado)

1. Abre **Windows PowerShell** (o PowerShell Core)
2. Navega a la carpeta `mhw-deployment`:
   ```powershell
   cd C:\ruta\a\tu\proyecto\ticket-2\mhw-deployment
   ```
3. Arrastra el archivo **Deploy-Interactive.ps1** a la ventana de PowerShell
4. Presiona **Enter**

### Método 2: Ejecución Directa

```powershell
cd C:\ruta\a\tu\proyecto\ticket-2\mhw-deployment
.\Deploy-Interactive.ps1
```

### Método 3: Continuar desde una Fase Específica

Si el deployment se interrumpe, puedes continuar desde una fase específica:

```powershell
# Continuar desde Fase 3 (Docker Build)
.\Deploy-Interactive.ps1 -FromPhase 3

# Continuar desde Fase 5 (SSL Certificate)
.\Deploy-Interactive.ps1 -FromPhase 5
```

### Método 4: Saltar Validación (No Recomendado)

```powershell
# Solo usar si estás 100% seguro de que las credenciales están OK
.\Deploy-Interactive.ps1 -SkipValidation
```

---

## 📊 Fases del Deployment

El script ejecuta 7 fases en orden:

### Fase 1: Habilitar APIs de GCP
- Habilita todas las APIs necesarias (Cloud Run, Compute, Secret Manager, etc.)
- **Tiempo estimado**: 2-3 minutos

### Fase 2: Docker Build & Push
- Configura autenticación Docker para GCP
- Build de imagen usando Cloud Build (recomendado) o build local
- Push a Artifact Registry
- **Tiempo estimado**: 5-10 minutos

### Fase 3: Cloud Run Deployment
- Despliega el servicio a Cloud Run
- Configura secrets, variables de entorno, Cloud SQL Proxy
- Configura recursos (CPU, RAM, instancias)
- **Tiempo estimado**: 3-5 minutos

### Fase 4: Load Balancer & NEG
- Crea Network Endpoint Group (serverless)
- Configura Backend Service
- **Tiempo estimado**: 2-3 minutos

### Fase 5: SSL Certificate & HTTPS Proxy
- Crea certificado SSL administrado por Google
- Configura URL Map y HTTPS Proxy
- **Tiempo estimado**: 2-3 minutos (+ 15-60 min para provisioning de SSL)

### Fase 6: IP Estática & Forwarding Rule
- Reserva IP estática global
- Crea Forwarding Rule para HTTPS
- **Requiere**: Configurar DNS manualmente
- **Tiempo estimado**: 2-3 minutos

### Fase 7: IAP (Identity-Aware Proxy)
- Configura autenticación con Google SSO
- **Requiere**: Pasos manuales en consola web
- **Tiempo estimado**: 5-10 minutos (manual)

**Tiempo total**: 25-35 minutos (excluyendo provisioning de SSL)

---

## 🎨 Características Visuales

### Banner de Bienvenida

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║   ████████╗██╗ ██████╗██╗  ██╗███████╗████████╗    ██╗  ██╗ ██████╗ ███╗   ███╗███████╗
║   ╚══██╔══╝██║██╔════╝██║ ██╔╝██╔════╝╚══██╔══╝    ██║  ██║██╔═══██╗████╗ ████║██╔════╝
║      ██║   ██║██║     █████╔╝ █████╗     ██║       ███████║██║   ██║██╔████╔██║█████╗
║      ██║   ██║██║     ██╔═██╗ ██╔══╝     ██║       ██╔══██║██║   ██║██║╚██╔╝██║██╔══╝
║      ██║   ██║╚██████╗██║  ██╗███████╗   ██║       ██║  ██║╚██████╔╝██║ ╚═╝ ██║███████╗
║      ╚═╝   ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝   ╚═╝       ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝
║                                                                    ║
║                   🚀 DEPLOYMENT INTERACTIVO - GCP 🚀               ║
║                         Versión 1.0 Beta RS                        ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

### Pool de Mensajes Aleatorios (54 items)

Cada vez que ejecutas el script, verás un mensaje diferente. Ejemplos:

**ASCII Art:**
- Docker Container
- Cloud con mensaje
- Cohete
- Base de datos
- Servidor
- Candado de seguridad
- Trofeo de éxito

**Frases Motivacionales:**
- "Code is like humor. When you have to explain it, it's bad."
- "First, solve the problem. Then, write the code."
- "Talk is cheap. Show me the code."

**Chistes Tech:**
- "Why do programmers prefer dark mode? Because light attracts bugs! 🐛💡"
- "A SQL query walks into a bar, walks up to two tables and asks... 'Can I JOIN you?'"
- "99 little bugs in the code... 127 little bugs in the code"

**Datos Curiosos:**
- "The first computer bug was an actual bug (a moth) found in 1947"
- "Google uses over 1,000,000 servers worldwide"
- "GCP has 35+ regions and 106+ zones worldwide"

### Iconos de Estado

El script usa iconos consistentes para feedback visual:

- `[⏳]` - Paso en progreso
- `[✅]` - Éxito
- `[❌]` - Error
- `[📍]` - Información adicional
- `[⚠️ ]` - Advertencia

### Colores

- **Cyan**: Pasos en progreso, headers secundarios
- **Green**: Mensajes de éxito
- **Red**: Errores
- **Yellow**: Información adicional, advertencias
- **Magenta**: Headers principales, bordes decorativos
- **Gray**: Mensajes de espera

---

## ⚙️ Configuración

### Archivo config.env

Puedes crear un archivo `config.env` para personalizar los valores (opcional):

```bash
# config.env
GCP_PROJECT_ID=tu-proyecto-gcp
GCP_REGION=us-central1
CLOUD_SQL_INSTANCE=nombre-instancia-sql
SERVICE_ACCOUNT_EMAIL=tu-sa@proyecto.iam.gserviceaccount.com
CLOUD_RUN_SERVICE=nombre-servicio-cloud-run
DOCKER_IMAGE_NAME=nombre-imagen
ARTIFACT_REGISTRY_REPO=nombre-repo
```

**Nota**: Si no existe `config.env`, el script usa valores por defecto para `ticket-home-demo`.

### Modificar Configuración Directamente

También puedes editar el script `Deploy-Interactive.ps1` y modificar el objeto `$Config`:

```powershell
$Config = @{
    GCP_PROJECT_ID = "tu-proyecto"
    GCP_REGION = "us-central1"
    # ... etc
}
```

---

## 🐛 Troubleshooting

### Error: "No se encontró el módulo DeploymentFunctions.psm1"

**Causa**: El script no puede encontrar el módulo de funciones.

**Solución**:
1. Verifica que estés ejecutando el script desde la carpeta `mhw-deployment`
2. Verifica que exista el archivo `lib/DeploymentFunctions.psm1`
3. Estructura correcta:
   ```
   mhw-deployment/
   ├── Deploy-Interactive.ps1
   ├── lib/
   │   ├── DeploymentFunctions.psm1
   │   └── WelcomeMessages.json
   └── docs/
       └── DEPLOY_INTERACTIVE_README.md
   ```

### Error: "Docker Desktop no está corriendo"

**Causa**: Docker daemon no está activo.

**Solución**:
1. Inicia Docker Desktop
2. Espera a que el ícono de Docker muestre "Running"
3. Verifica con: `docker ps`

### Error: "No autenticado en gcloud"

**Causa**: No has autenticado gcloud CLI.

**Solución**:
```powershell
gcloud auth login
gcloud config set project tu-proyecto-id
```

### Error: "Secret no encontrado: mhw-database-url"

**Causa**: Los secrets no existen en Secret Manager.

**Solución**:
1. Crea los secrets siguiendo el README.md principal
2. Verifica con:
   ```powershell
   gcloud secrets list --project=tu-proyecto
   ```

### Error: "Cloud Build falló"

**Causa**: Error en el build de la imagen Docker.

**Solución**:
1. Revisa los logs de Cloud Build en la consola GCP
2. Verifica que el Dockerfile esté correcto
3. Verifica que tengas permisos de Cloud Build en el proyecto

### Advertencia: "Proyecto actual diferente al esperado"

El script te preguntará si deseas cambiar al proyecto correcto. Responde `S` para cambiar automáticamente.

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Deployment Completo desde Cero

```powershell
cd C:\proyectos\ticket-2\mhw-deployment
.\Deploy-Interactive.ps1

# El script mostrará:
# 1. Banner de bienvenida → [ENTER]
# 2. Mensaje aleatorio entretenido → [ENTER]
# 3. Validación de credenciales
# 4. Confirmar deployment → [S/n]: S
# 5. Fase 1: APIs → [ENTER]
# 6. Fase 2: Docker Build → [ENTER]
# ... etc
```

### Ejemplo 2: Reintentar desde Fase de Docker

Si el build falló por un error de red:

```powershell
.\Deploy-Interactive.ps1 -FromPhase 2
```

### Ejemplo 3: Deployment sin Validación (Avanzado)

```powershell
# Solo si estás seguro de que todo está OK
.\Deploy-Interactive.ps1 -SkipValidation -FromPhase 2
```

---

## 🔒 Seguridad

### Buenas Prácticas

1. **NUNCA** compartas secrets o contraseñas en el código
2. Todos los secrets deben estar en Google Secret Manager
3. Service Account con **principio de menor privilegio**
4. Habilita IAP para autenticación robusta
5. Usa certificados SSL administrados por Google

### Permisos Mínimos Requeridos

El script necesita estos permisos en GCP:

```yaml
roles:
  - roles/run.admin          # Cloud Run
  - roles/compute.admin      # Load Balancer, NEG, SSL
  - roles/cloudsql.client    # Cloud SQL Proxy
  - roles/secretmanager.secretAccessor  # Secrets
  - roles/iam.serviceAccountUser  # Service Account
  - roles/iap.admin          # IAP
```

---

## 🆘 Soporte

### Reportar Issues

Si encuentras un problema:

1. Ejecuta el script con `-Verbose` para más detalles
2. Copia el error completo (stack trace)
3. Crea un issue en GitHub con:
   - Versión de PowerShell: `$PSVersionTable`
   - Versión de gcloud: `gcloud --version`
   - Descripción del error
   - Pasos para reproducir

### Recursos Adicionales

- [Documentación GCP Cloud Run](https://cloud.google.com/run/docs)
- [Documentación IAP](https://cloud.google.com/iap/docs)
- [README.md principal](../README.md) - Guía completa de deployment
- [deploy-master.sh](../deploy-master.sh) - Script bash equivalente

---

## 📚 Referencia de Funciones

### Módulo DeploymentFunctions.psm1

#### Funciones de Output

- `Write-Step` - Muestra paso en progreso
- `Write-Success` - Mensaje de éxito
- `Write-Error` - Mensaje de error
- `Write-Info` - Información adicional
- `Write-Warning` - Advertencia
- `Write-Header` - Header decorativo

#### Funciones de Interacción

- `Wait-UserInput` - Pausa para presionar Enter
- `Confirm-Action` - Confirmación S/n

#### Funciones de Validación

- `Test-GCloudAuth` - Verifica autenticación gcloud
- `Test-GCloudProject` - Verifica proyecto GCP
- `Test-CloudSQLInstance` - Verifica Cloud SQL
- `Test-Secrets` - Verifica secrets en Secret Manager
- `Test-ServiceAccount` - Verifica Service Account
- `Test-Docker` - Verifica Docker Desktop

#### Funciones de Deployment

- `Invoke-CommandWithFeedback` - Ejecuta comando con feedback
- `Measure-DeploymentTime` - Mide tiempo de operación
- `Show-Banner` - Muestra banner de bienvenida
- `Show-RandomWelcome` - Mensaje aleatorio del pool

---

## 🎯 Próximos Pasos Después del Deployment

Una vez completado el deployment:

1. **Verificar SSL Certificate**
   ```powershell
   gcloud compute ssl-certificates describe tickethome-demo-ssl `
     --global --project=ticket-home-demo `
     --format="get(managed.status)"
   ```
   Debe mostrar: `ACTIVE` (puede tardar 15-60 min)

2. **Probar Acceso**
   - Accede a tu dominio: `https://tu-dominio.com`
   - Debe redirigir a login de Google (IAP)
   - Autentícate con usuario autorizado

3. **Verificar Superusuarios**
   - Conecta a Cloud SQL
   - Verifica tabla `superuser`
   - Agrega emails si es necesario

4. **Seed de Base de Datos** (opcional)
   - Ejecuta `flask reset-db` en Cloud Run
   - O ejecuta scripts SQL desde `_sql/`

5. **Monitoring**
   - Revisa logs: `gcloud logging tail ...`
   - Configura alertas en Cloud Monitoring
   - Verifica métricas de Cloud Run

---

## 📄 Licencia y Créditos

**Creado por**: Claude (Anthropic)
**Proyecto**: Ticket Home - RedSalud Chile
**Versión**: 1.0 Beta RS
**Fecha**: 2025-11-15

---

## 🚀 ¡Listo para Desplegar!

```powershell
cd mhw-deployment
.\Deploy-Interactive.ps1
```

**¡Que tengas un deployment exitoso!** 🎉
