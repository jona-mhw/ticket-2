# 🔐 Guía de Secretos - Todos los Ambientes

**Última actualización**: 2025-11-15

---

## 📋 Resumen de Secretos por Ambiente

| Ambiente | Secret Name | Contiene | Proyecto GCP |
|----------|-------------|----------|--------------|
| **MHW DEV** | `mhw-database-url` | PostgreSQL connection string | ticket-home-demo |
| **MHW DEV** | `mhw-secret-key` | Flask SECRET_KEY | ticket-home-demo |
| **MHW DEV** | `mhw-superuser-emails` | Lista de emails admin | ticket-home-demo |
| **Empresa DEV** | `tickethome-db-url` | PostgreSQL connection string | dev-ticket-home-redsalud |
| **Empresa DEV** | `tickethome-secret-key` | Flask SECRET_KEY | dev-ticket-home-redsalud |
| **Empresa DEV** | `superuser-emails` | Lista de emails admin | dev-ticket-home-redsalud |
| **Empresa QA** | `tickethome-db-url` | PostgreSQL connection string | qa-ticket-home-redsalud |
| **Empresa QA** | `tickethome-secret-key` | Flask SECRET_KEY | qa-ticket-home-redsalud |
| **Empresa QA** | `superuser-emails` | Lista de emails admin | qa-ticket-home-redsalud |

---

## 🚀 Setup Rápido

### MHW DEV (Tu Cloud Personal)

```bash
# 1. Configurar proyecto
gcloud config set project ticket-home-demo

# 2. Generar SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
echo "Guarda este SECRET_KEY: $SECRET_KEY"

# 3. Crear DATABASE_URL secret
# Formato Unix socket para Cloud SQL Proxy
echo "postgresql://mhw_user:TU_PASSWORD@/mhw_ticket_home?host=/cloudsql/ticket-home-demo:us-central1:tickethome-db" | \
  gcloud secrets create mhw-database-url \
  --data-file=- \
  --project=ticket-home-demo

# 4. Crear SECRET_KEY secret
echo "$SECRET_KEY" | \
  gcloud secrets create mhw-secret-key \
  --data-file=- \
  --project=ticket-home-demo

# 5. Crear SUPERUSER_EMAILS secret
echo "tu.email@gmail.com;otro.email@example.com" | \
  gcloud secrets create mhw-superuser-emails \
  --data-file=- \
  --project=ticket-home-demo

# 6. Dar permisos al Service Account
gcloud secrets add-iam-policy-binding mhw-database-url \
  --member="serviceAccount:tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=ticket-home-demo

gcloud secrets add-iam-policy-binding mhw-secret-key \
  --member="serviceAccount:tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=ticket-home-demo

gcloud secrets add-iam-policy-binding mhw-superuser-emails \
  --member="serviceAccount:tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=ticket-home-demo
```

### Empresa DEV

```batch
REM Ejecutar desde deployment/empresa-dev/
0-setup-secrets.bat
```

O manualmente:

```bash
# 1. Configurar proyecto
gcloud config set project dev-ticket-home-redsalud

# 2. Crear SECRET_KEY (si no existe)
echo "TU_SECRET_KEY_GENERADO" | \
  gcloud secrets create tickethome-secret-key \
  --data-file=- \
  --project=dev-ticket-home-redsalud

# 3. Crear SUPERUSER_EMAILS
echo "global_admin@tickethome.com;jonathan.segura@redsalud.cl;admin@tickethome.com" | \
  gcloud secrets create superuser-emails \
  --data-file=- \
  --project=dev-ticket-home-redsalud

# 4. Dar permisos al Service Account
gcloud secrets add-iam-policy-binding superuser-emails \
  --member="serviceAccount:dev-ticket-home@dev-ticket-home-redsalud.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=dev-ticket-home-redsalud
```

### Empresa QA

```batch
REM Ejecutar desde deployment/empresa-qa/
0-setup-secrets.bat
```

O manualmente (similar a Empresa DEV pero con proyecto qa-ticket-home-redsalud).

---

## 📝 Formato de Cada Secret

### DATABASE_URL

**Formato para MHW DEV** (Cloud SQL Proxy con Unix Socket):
```
postgresql://USER:PASSWORD@/DATABASE?host=/cloudsql/PROJECT:REGION:INSTANCE
```

**Ejemplo MHW DEV**:
```
postgresql://mhw_user:ZHB5ChBBB3IWRLSi8WvQhrBkuQFUljQNMBlStNTkQJM@/mhw_ticket_home?host=/cloudsql/ticket-home-demo:us-central1:tickethome-db
```

**Formato para Empresa DEV/QA** (VPC Connector con IP privada):
```
postgresql://USER:PASSWORD@IP_PRIVADA:5432/DATABASE
```

**Ejemplo Empresa DEV**:
```
postgresql://dev_user:PASSWORD@10.X.X.X:5432/dev_ticket_home
```

### SECRET_KEY

**Generación**:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Ejemplo**:
```
c89554257e2e8b5794f76745a5c810d9cfa359a0e15d56cd7013f6ee4c402ef6
```

**Longitud**: 64 caracteres hexadecimales (32 bytes)

### SUPERUSER_EMAILS

**Formato**: Emails separados por punto y coma (;)

**Ejemplo**:
```
admin@tickethome.com;jonathan.segura@redsalud.cl;tu.email@gmail.com
```

⚠️ **Importante**: No dejar espacios entre emails, solo `;`

---

## 🔄 Actualizar un Secret Existente

```bash
# Crear nueva versión del secret
echo "NUEVO_VALOR" | \
  gcloud secrets versions add NOMBRE_SECRET \
  --data-file=- \
  --project=PROYECTO

# Ejemplo: Actualizar superuser emails en MHW DEV
echo "nuevo.admin@example.com;jonathan.segura.vega@gmail.com" | \
  gcloud secrets versions add mhw-superuser-emails \
  --data-file=- \
  --project=ticket-home-demo

# Re-deploy Cloud Run para usar nueva versión
gcloud run services update tickethome-demo \
  --region=us-central1 \
  --project=ticket-home-demo
```

---

## 👁️ Ver Valor de un Secret

```bash
# MHW DEV
gcloud secrets versions access latest \
  --secret=mhw-superuser-emails \
  --project=ticket-home-demo

# Empresa DEV
gcloud secrets versions access latest \
  --secret=superuser-emails \
  --project=dev-ticket-home-redsalud

# Empresa QA
gcloud secrets versions access latest \
  --secret=superuser-emails \
  --project=qa-ticket-home-redsalud
```

---

## 🗑️ Eliminar un Secret (Con Cuidado)

```bash
# ADVERTENCIA: Esto eliminará el secret permanentemente
gcloud secrets delete NOMBRE_SECRET \
  --project=PROYECTO

# Ejemplo
gcloud secrets delete mhw-superuser-emails \
  --project=ticket-home-demo
```

---

## ✅ Verificar Permisos del Service Account

```bash
# MHW DEV
gcloud secrets get-iam-policy mhw-database-url \
  --project=ticket-home-demo

# Debe mostrar:
# - serviceAccount:tickethome-demo-sa@ticket-home-demo.iam.gserviceaccount.com
# - role: roles/secretmanager.secretAccessor

# Empresa DEV
gcloud secrets get-iam-policy superuser-emails \
  --project=dev-ticket-home-redsalud

# Debe mostrar:
# - serviceAccount:dev-ticket-home@dev-ticket-home-redsalud.iam.gserviceaccount.com
# - role: roles/secretmanager.secretAccessor
```

---

## 🔐 Mejores Prácticas

### ✅ DO (Hacer)

1. **Usar Secret Manager** para todas las credenciales
2. **Rotar secrets** periódicamente (cada 90 días)
3. **Dar permisos mínimos** a Service Accounts
4. **Separar secrets por ambiente** (nunca compartir entre ambientes)
5. **Documentar qué contiene cada secret**
6. **Versionar secrets** (crear nueva versión en lugar de editar)

### ❌ DON'T (No Hacer)

1. **NO** poner secrets en variables de entorno de Cloud Run
2. **NO** commitear secrets en git
3. **NO** compartir secrets entre proyectos
4. **NO** usar mismo SECRET_KEY en múltiples ambientes
5. **NO** dejar secrets sin permisos configurados
6. **NO** eliminar secrets sin backup

---

## 🐛 Troubleshooting

### Error: "Permission denied accessing secret"

**Causa**: Service Account no tiene permisos.

**Solución**:
```bash
gcloud secrets add-iam-policy-binding NOMBRE_SECRET \
  --member="serviceAccount:SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor" \
  --project=PROYECTO
```

### Error: "Secret not found"

**Causa**: Secret no existe en ese proyecto.

**Solución**: Crear el secret siguiendo la guía de arriba.

### Error: "Connection to database failed"

**Causa**: DATABASE_URL mal formateado o credenciales incorrectas.

**Solución**:
1. Verificar formato de DATABASE_URL
2. Verificar password de base de datos
3. Verificar connection string (Unix socket vs IP)

### Error: "No superusers found"

**Causa**: SUPERUSER_EMAILS vacío o mal formateado.

**Solución**:
```bash
# Verificar valor actual
gcloud secrets versions access latest --secret=mhw-superuser-emails --project=ticket-home-demo

# Debe retornar algo como: email1@example.com;email2@example.com
```

---

## 📋 Checklist de Setup de Secrets

### MHW DEV
- [ ] `mhw-database-url` creado
- [ ] `mhw-secret-key` creado
- [ ] `mhw-superuser-emails` creado
- [ ] Permisos asignados a `tickethome-demo-sa`
- [ ] Secrets verificados con `gcloud secrets versions access`

### Empresa DEV
- [ ] `tickethome-db-url` existe (ya creado)
- [ ] `tickethome-secret-key` existe (ya creado)
- [ ] `superuser-emails` creado (v1.9.2+)
- [ ] Permisos asignados a `dev-ticket-home@dev-ticket-home-redsalud.iam.gserviceaccount.com`

### Empresa QA
- [ ] `tickethome-db-url` existe (ya creado)
- [ ] `tickethome-secret-key` existe (ya creado)
- [ ] `superuser-emails` creado (v1.9.2+)
- [ ] Permisos asignados a `qa-ticket-home@qa-ticket-home-redsalud.iam.gserviceaccount.com`

---

## 📞 Soporte

**Dudas sobre secrets**: Ver documentación de Google Secret Manager
- https://cloud.google.com/secret-manager/docs

**Problemas con deployment**: Ver `deployment/README.md`

---

**Creado por**: Jonathan Segura
**Última actualización**: 2025-11-15
