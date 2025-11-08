# 🚀 GitHub Actions Workflows

CI/CD automatizado para Ticket Home.

## 📁 Workflows Disponibles

### 1. `ci.yml` - Continuous Integration

**Trigger**: Automático en PRs y push a `main`

**Jobs**:
- **tests**: Ejecuta pytest con PostgreSQL
  - Coverage report (XML, HTML, terminal)
  - Upload a Codecov
  - Artifacts de coverage guardados 7 días

- **lint**: Linting y calidad de código
  - Black (code formatting)
  - isort (import sorting)
  - Flake8 (style guide)

- **security**: Escaneo de seguridad
  - Safety (vulnerabilidades en dependencias)
  - Bandit (security linter)

**Quality Gates**:
- ✅ Todos los tests deben pasar
- ✅ Black formatting correcto
- ✅ isort imports ordenados
- ✅ Sin errores críticos de Flake8

---

### 2. `deploy-qa.yml` - Deploy to QA

**Trigger**:
- Automático en merge/push a `main`
- Manual via `workflow_dispatch`

**Proceso**:
1. Build imagen Docker
2. Push a Artifact Registry
3. Deploy a Cloud Run QA
4. Configurar IAP policy
5. Summary con URL del servicio

**Configuración QA**:
- **URL**: https://qa-ticket-home.mhwdev.dev
- **Min instances**: 1
- **Max instances**: 3
- **CPU**: 2 vCPUs
- **Memory**: 1 GiB
- **VPC**: tckthome-conn-qa-sa-west1

**Secrets Requeridos**:
- `GCP_SA_KEY_QA` - Service Account JSON

---

### 3. `deploy-prod.yml` - Deploy to PRODUCTION

**Trigger**: Solo manual (`workflow_dispatch`)

**Inputs Requeridos**:
- `confirm_production`: Debe escribir "DEPLOY TO PRODUCTION"
- `version_tag`: Tag de versión (ej: v1.0.0)

**Proceso**:
1. Validar confirmación
2. Build imagen Docker con version tag
3. Push a Artifact Registry PROD
4. Deploy a Cloud Run PROD
5. Configurar IAP policy
6. Crear GitHub Release
7. Summary del deployment

**Configuración PROD**:
- **URL**: https://ticket-home.redsalud.cl
- **Min instances**: 2
- **Max instances**: 10
- **CPU**: 4 vCPUs
- **Memory**: 2 GiB
- **VPC**: tckthome-conn-prod-sa-west1

**Secrets Requeridos**:
- `GCP_SA_KEY_PROD` - Service Account JSON

---

## 🔑 Configuración de Secrets

Configura estos secrets en GitHub: **Settings → Secrets and variables → Actions**

### Required Secrets

| Secret | Descripción | Usado en |
|--------|-------------|----------|
| `GCP_SA_KEY_QA` | Service Account JSON para QA | deploy-qa.yml |
| `GCP_SA_KEY_PROD` | Service Account JSON para PROD | deploy-prod.yml |
| `CODECOV_TOKEN` | Token de Codecov (opcional) | ci.yml |
| `SLACK_WEBHOOK_URL` | Webhook de Slack (opcional) | deploy-prod.yml |

### Crear Service Account Key

```bash
# Para QA
gcloud iam service-accounts keys create key-qa.json \
  --iam-account=github-actions-qa@tickethome-mhw.iam.gserviceaccount.com

# Para PROD
gcloud iam service-accounts keys create key-prod.json \
  --iam-account=github-actions-prod@tickethome-prod.iam.gserviceaccount.com
```

Luego copia el contenido del JSON en el secret correspondiente.

---

## 📖 Uso

### PR Workflow (Automático)

1. Crea un PR a `main`
2. CI se ejecuta automáticamente
3. Revisa los checks antes de mergear
4. Al mergear, deploy a QA es automático

### Deploy a QA (Manual)

1. Ve a **Actions** → **Deploy to QA**
2. Click **Run workflow**
3. Selecciona branch `main`
4. Click **Run workflow**

### Deploy a PRODUCTION (Manual)

⚠️ **IMPORTANTE**: Solo para releases verificados

1. Ve a **Actions** → **Deploy to PRODUCTION**
2. Click **Run workflow**
3. Ingresa:
   - Confirmation: `DEPLOY TO PRODUCTION`
   - Version tag: `v1.0.0`
4. Click **Run workflow**
5. **Requiere aprobación** en environment "Production"
6. Se crea GitHub Release automáticamente

---

## 🎯 Best Practices

### Antes de mergear a main

- ✅ Todos los tests pasan en CI
- ✅ Code review aprobado
- ✅ Cambios probados localmente
- ✅ Changelog actualizado

### Deploy a QA

- ✅ Es automático después del merge
- ✅ Verifica que el deploy fue exitoso
- ✅ Prueba la funcionalidad en QA

### Deploy a PROD

- ⚠️ Solo deploy código ya probado en QA
- ⚠️ Actualiza changelog antes de deploy
- ⚠️ Usa semantic versioning (v1.0.0, v1.1.0, v2.0.0)
- ⚠️ Notifica al equipo del deploy

---

## 🐛 Troubleshooting

### CI fails con error de PostgreSQL

**Problema**: Tests fallan porque no pueden conectar a DB

**Solución**: El workflow ya configura PostgreSQL. Verifica que `DATABASE_URL` esté correcta en env vars.

### Deploy falla con error 403

**Problema**: Service Account no tiene permisos

**Solución**:
```bash
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:github-actions@[PROJECT_ID].iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Tests pasan localmente pero fallan en CI

**Problema**: Diferencias de ambiente

**Solución**:
- Verifica Python version (debe ser 3.11)
- Revisa variables de entorno en workflow
- Corre tests con `pytest -v` para más detalle

---

## 📊 Monitoring

### Ver status de workflows

- **Actions tab** en GitHub
- Filtrar por workflow name
- Ver logs detallados de cada job

### Coverage reports

- Automáticamente subido a Codecov
- HTML report disponible en Artifacts (7 días)
- Download desde Actions → Run → Artifacts

### Deployment logs

- Cloud Run logs en GCP Console
- Real-time logs: `gcloud run services logs read ticket-home-qa --region=southamerica-west1`

---

## 🔄 Flujo Completo

```
PR creado
    ↓
CI ejecuta (tests + lint + security)
    ↓
PR aprobado y merged a main
    ↓
Deploy automático a QA
    ↓
Testing en QA
    ↓
Deploy manual a PROD (con aprobación)
    ↓
GitHub Release creado
```

---

## 🔗 Referencias

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Pytest Docs](https://docs.pytest.org/)
