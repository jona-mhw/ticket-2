# Scripts de Deployment - Ticket Home

## 📋 Estructura de Scripts

### 0. Setup Inicial (Una sola vez)
```
0-setup-secrets.bat
```
**Cuándo usar**: Solo la primera vez o cuando cambies superuser emails.
Crea los secrets en Google Secret Manager (DEV y QA).

---

### DEV (ticket-home.mhwdev.dev)

#### 1. Build & Push
```
1-build-push-DEV.bat
```
**Cuándo usar**: Siempre antes de deployar.
Construye la imagen Docker y la sube a Artifact Registry.

#### 2. Deploy con Reset DB
```
2-deploy-DEV-reset-db.bat
```
**Cuándo usar**:
- Primera vez deployando
- Cambios en `models.py` (tablas/campos nuevos)

⚠️ **Advertencia**: Borra y recrea la base de datos.

#### 3. Deploy Normal
```
3-deploy-DEV-normal.bat
```
**Cuándo usar**:
- Cambios de código (HTML, CSS, JS, Python)
- **NO** cambios en base de datos

✅ **Recomendado**: Uso más común.

---

### QA (qa-ticket-home.mhwdev.dev)

#### 1. Build & Push
```
1-build-push-QA.bat
```
Igual que DEV pero para proyecto QA.

#### 2. Deploy con Reset DB
```
2-deploy-QA-reset-db.bat
```
Igual que DEV pero con:
- Grupo IAP: `qa-ticket-home-rs@googlegroups.com`
- Login tradicional **DESHABILITADO** (solo SSO)

#### 3. Deploy Normal
```
3-deploy-QA-normal.bat
```
Igual que DEV pero para QA (sin reset DB).

---

## 🚀 Flujo Normal de Deployment

### Para cambios de código (más común)
```bash
# 1. Build & push
1-build-push-DEV.bat  # o 1-build-push-QA.bat

# 2. Deploy normal
3-deploy-DEV-normal.bat  # o 3-deploy-QA-normal.bat
```

### Para cambios en base de datos
```bash
# 1. Build & push
1-build-push-DEV.bat

# 2. Deploy con reset
2-deploy-DEV-reset-db.bat
```

---

## 🔐 Diferencias entre Ambientes

| Característica | DEV | QA |
|----------------|-----|-----|
| **URL** | ticket-home.mhwdev.dev | qa-ticket-home.mhwdev.dev |
| **Grupo IAP** | rs-ticket-home@googlegroups.com | qa-ticket-home-rs@googlegroups.com |
| **Login Tradicional** | ✅ Habilitado | ❌ Solo SSO |
| **VPC Connector** | tckthome-conn-sa-west1 | tckthome-conn-qa-sa-west1 |

---

## 📝 Secrets Usados

Los scripts de deployment usan estos secrets automáticamente:
- `DATABASE_URL` - URL conexión PostgreSQL
- `SECRET_KEY` - Clave Flask
- `SUPERUSER_EMAILS` - Emails de superusuarios (v1.9.2+)

**Actualizar secrets**: Ver `RESUMEN-SEGURIDAD-v1.9.3.md` sección "Secrets".

---

## ⚠️ Importante

- **Siempre** ejecuta `1-build-push` antes de deployar
- Scripts `2-deploy-*-reset-db.bat` **borran datos**
- IAM policy binding se aplica automáticamente
- Si ves 403 Forbidden, verifica que estés en el Google Group correcto

---

**Versión**: v1.9.3 Security Hardening
**Última actualización**: 2025-11-02
