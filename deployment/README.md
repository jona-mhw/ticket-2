# 🚀 Deployment Guide - Ticket Home

**Última actualización**: 2025-11-15
**Versión**: 2.0

---

## 📊 Ambientes Disponibles

| Ambiente | Propósito | Región GCP | Proyecto GCP | Scripts |
|----------|-----------|------------|--------------|---------|
| **LOCAL** | Desarrollo diario en tu máquina | N/A | N/A | `deployment/local/` |
| **MHW DEV** | **Tu ambiente principal de desarrollo cloud** | us-central1 | ticket-home-demo | `deployment/mhw-dev/` |
| **Empresa DEV** | Testing funcional RedSalud | southamerica-west1 | dev-ticket-home-redsalud | `deployment/empresa-dev/` |
| **Empresa QA** | Pre-producción RedSalud | southamerica-west1 | qa-ticket-home-redsalud | `deployment/empresa-qa/` |

---

## 🎯 ¿Qué Ambiente Usar?

### 📝 Desarrollo Diario (80% del tiempo)
→ **LOCAL** - `flask run`
- Más rápido
- Sin costos cloud
- Debugging inmediato

### 🚀 Desarrollo Cloud / Testing IAP / Demos (15% del tiempo)
→ **MHW DEV** - `deployment/mhw-dev/Deploy-Interactive.ps1`
- Tu nube personal
- Experimenta libremente
- Testing de deployment
- Demos a clientes

### 🏢 Testing con Infraestructura RedSalud (4% del tiempo)
→ **Empresa DEV** - `deployment/empresa-dev/3-deploy-normal.bat`
- VPC Connector
- Región Chile
- Testing funcional

### ✅ Validación Pre-Producción (1% del tiempo)
→ **Empresa QA** - `deployment/empresa-qa/3-deploy-normal.bat`
- Solo SSO (sin login tradicional)
- Grupo IAP separado
- Testing final antes de producción

---

## 📁 Estructura de Deployment

```
deployment/
├── README.md                    # Este archivo
│
├── local/                       # Desarrollo local
│   ├── README.md
│   ├── setup-local.sh
│   ├── setup-local.bat
│   └── .env.local.example
│
├── mhw-dev/                     # Tu cloud personal (PRINCIPAL)
│   ├── README.md
│   ├── Deploy-Interactive.ps1   # Script interactivo multi-ambiente
│   ├── deploy-master.sh
│   ├── configs/
│   │   ├── mhw-dev.env         # Config MHW DEV
│   │   ├── empresa-dev.env     # Config Empresa DEV
│   │   └── empresa-qa.env      # Config Empresa QA
│   ├── lib/
│   │   └── DeploymentFunctions.psm1
│   └── docs/
│       ├── DEPLOY_INTERACTIVE_README.md
│       └── SECRETS_GUIDE.md     # NUEVO
│
├── empresa-dev/                 # RedSalud DEV
│   ├── README.md
│   ├── 0-setup-secrets.bat
│   ├── 1-build-push-local.bat  # Build con Docker Desktop
│   ├── 2-deploy-normal.bat
│   └── 3-deploy-reset-db.bat
│
└── empresa-qa/                  # RedSalud QA
    ├── README.md
    ├── 0-setup-secrets.bat
    ├── 1-build-push-local.bat
    ├── 2-deploy-normal.bat
    └── 3-deploy-reset-db.bat
```

---

## 🚀 Quick Start por Ambiente

### LOCAL
```bash
# Setup inicial (solo primera vez)
cd deployment/local
./setup-local.sh  # o setup-local.bat en Windows

# Desarrollo diario
flask run
```

### MHW DEV (Tu Ambiente Principal)
```powershell
cd deployment/mhw-dev

# Opción 1: Script interactivo (recomendado)
.\Deploy-Interactive.ps1
# Te preguntará a qué ambiente apuntar

# Opción 2: Bash script
./deploy-master.sh
```

### Empresa DEV
```batch
cd deployment\empresa-dev

REM 1. Build con Docker Desktop
1-build-push-local.bat

REM 2. Deploy normal (sin reset DB)
2-deploy-normal.bat
```

### Empresa QA
```batch
cd deployment\empresa-qa

REM 1. Build con Docker Desktop
1-build-push-local.bat

REM 2. Deploy normal (sin reset DB)
2-deploy-normal.bat
```

---

## 🔐 Secretos Requeridos por Ambiente

Cada ambiente necesita sus propios secretos en Google Secret Manager.

### MHW DEV
- `mhw-database-url`
- `mhw-secret-key`
- `mhw-superuser-emails`

### Empresa DEV
- `tickethome-db-url`
- `tickethome-secret-key`
- `superuser-emails`

### Empresa QA
- `tickethome-db-url`
- `tickethome-secret-key`
- `superuser-emails`

Ver guía completa: [`mhw-dev/docs/SECRETS_GUIDE.md`](mhw-dev/docs/SECRETS_GUIDE.md)

---

## 📊 Comparación de Ambientes

| Aspecto | LOCAL | MHW DEV | Empresa DEV | Empresa QA |
|---------|-------|---------|-------------|------------|
| **Región** | N/A | us-central1 🇺🇸 | southamerica-west1 🇨🇱 | southamerica-west1 🇨🇱 |
| **Proyecto GCP** | N/A | ticket-home-demo | dev-ticket-home-redsalud | qa-ticket-home-redsalud |
| **Autenticación** | Sin IAP | IAP + Demo Login | IAP + Demo Login | Solo IAP |
| **Conexión BD** | Local/Directa | Cloud SQL Proxy | VPC Connector | VPC Connector |
| **Build** | N/A | Cloud Build | Docker Desktop | Docker Desktop |
| **Min Instances** | N/A | 0 (escala a cero) | 1 | 1 |
| **Costos** | Gratis | **Tú pagas** 💰 | RedSalud paga | RedSalud paga |
| **URL** | localhost:5000 | ticket-home-beta.mhwdev.dev | ticket-home.mhwdev.dev | qa-ticket-home.mhwdev.dev |
| **Uso recomendado** | 80% | 15% | 4% | 1% |

---

## 📝 Workflows Recomendados

### Workflow 1: Feature Nueva (Normal)
```
1. Desarrollar en LOCAL (flask run)
2. Probar localmente
3. Commit a git
4. Deploy a MHW DEV (testing cloud)
5. Si todo OK → Deploy a Empresa DEV
6. Testing funcional en Empresa DEV
7. Si OK → Deploy a Empresa QA
8. Validación final
```

### Workflow 2: Cambio en Base de Datos (models.py)
```
1. Desarrollar en LOCAL
2. Crear migración Alembic
3. Probar migración en LOCAL
4. Deploy a MHW DEV con reset DB
5. Verificar seed funciona
6. Deploy a Empresa DEV con reset DB
7. Deploy a Empresa QA con reset DB
```

### Workflow 3: Experimentación / Demo
```
1. Desarrollar en LOCAL
2. Deploy directo a MHW DEV
3. Demo a clientes usando MHW DEV
```

---

## 🔧 Troubleshooting

### Error: "gcloud: command not found"
```bash
# Instalar gcloud CLI
# Windows: https://cloud.google.com/sdk/docs/install
# macOS: brew install --cask google-cloud-sdk
# Linux: curl https://sdk.cloud.google.com | bash
```

### Error: "Docker Desktop no está corriendo"
Solo aplica a Empresa DEV/QA (requieren Docker Desktop).
- Inicia Docker Desktop
- Verifica: `docker ps`

### Error: "Secret not found"
Ejecuta el script de setup de secrets para ese ambiente:
- MHW DEV: Ver `mhw-dev/docs/SECRETS_GUIDE.md`
- Empresa DEV: `empresa-dev/0-setup-secrets.bat`
- Empresa QA: `empresa-qa/0-setup-secrets.bat`

### Error: "403 Forbidden"
Verifica que estés en el Google Group correcto:
- MHW DEV: `ticket-home-demo@googlegroups.com`
- Empresa DEV: `rs-ticket-home@googlegroups.com`
- Empresa QA: `qa-ticket-home-rs@googlegroups.com`

---

## 📚 Documentación Detallada

- [Guía de Secretos](mhw-dev/docs/SECRETS_GUIDE.md) - Cómo crear y gestionar secretos
- [Script Interactivo](mhw-dev/docs/DEPLOY_INTERACTIVE_README.md) - Uso del Deploy-Interactive.ps1
- [Arquitectura](../docs/ARQUITECTURA.md) - Arquitectura técnica del proyecto
- [Deployment Log](../DEPLOYMENT_LOG.md) - Log detallado del primer deployment

---

## ❓ FAQ

**P: ¿Por qué MHW DEV usa us-central1 en lugar de southamerica-west1?**
R: Es tu cloud personal, puedes usar cualquier región. us-central1 suele tener más disponibilidad y a veces costos menores.

**P: ¿Por qué Empresa DEV/QA requieren Docker Desktop?**
R: Política/configuración de la empresa. Cloud Build está disponible pero no se usa.

**P: ¿Puedo usar el script interactivo para deployar a Empresa DEV/QA?**
R: ¡Sí! El script ahora pregunta a qué ambiente quieres deployar. Solo asegúrate de tener Docker Desktop corriendo.

**P: ¿Cuál es la diferencia entre MHW DEV y Empresa DEV?**
R: MHW DEV es tu cloud personal (tú pagas), Empresa DEV es de RedSalud (empresa paga). Arquitecturas ligeramente diferentes.

---

## 🎯 Próximos Pasos

1. **Configurar LOCAL** → `cd deployment/local && ./setup-local.sh`
2. **Configurar MHW DEV** → `cd deployment/mhw-dev && vim configs/mhw-dev.env`
3. **Primer deployment** → `.\Deploy-Interactive.ps1`

---

**Mantenido por**: Jonathan Segura
**Última revisión**: 2025-11-15
**Versión**: 2.0
