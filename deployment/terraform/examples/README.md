# Ejemplos de Terraform - Aprendizaje Gradual

Esta carpeta contiene ejemplos simples para aprender Terraform de forma progresiva.

## 📚 Orden Recomendado

1. **01-simple-secret** - Crear un secret en Secret Manager
2. **02-cloud-run-basic** - Crear un Cloud Run simple (imagen hello-world)
3. **03-cloud-run-with-secret** - Cloud Run que usa un secret
4. **04-load-balancer** - Load Balancer básico apuntando a Cloud Run

## 🎯 Cómo Usar Estos Ejemplos

### Paso 1: Elegir un Ejemplo

```bash
cd deployment/terraform/examples/01-simple-secret
```

### Paso 2: Configurar Variables

```bash
# Copiar archivo de ejemplo
cp terraform.tfvars.example terraform.tfvars

# Editar con tu proyecto GCP
vim terraform.tfvars
```

### Paso 3: Ejecutar Terraform

```bash
# Inicializar
terraform init

# Ver qué va a crear
terraform plan

# Crear el recurso
terraform apply

# Ver lo que se creó
terraform show

# Ver outputs
terraform output
```

### Paso 4: Experimentar

Haz cambios en `main.tf` y vuelve a ejecutar:

```bash
terraform plan
terraform apply
```

### Paso 5: Limpiar

```bash
# Destruir todo lo creado
terraform destroy
```

## 📖 Descripción de Ejemplos

### 01 - Simple Secret

**Qué aprenderás**:
- Sintaxis básica de Terraform
- Crear un recurso en GCP
- Usar variables
- Ver outputs

**Recurso creado**:
- 1 secret en Secret Manager

**Tiempo**: 5 minutos

---

### 02 - Cloud Run Basic

**Qué aprenderás**:
- Crear un Cloud Run service
- Configurar recursos (CPU, memoria)
- Hacer el servicio público

**Recurso creado**:
- 1 Cloud Run service (imagen hello-world de Google)

**Tiempo**: 10 minutos

---

### 03 - Cloud Run with Secret

**Qué aprenderás**:
- Crear múltiples recursos relacionados
- Montar secrets en Cloud Run
- Referencias entre recursos

**Recursos creados**:
- 1 secret en Secret Manager
- 1 Cloud Run service que usa el secret

**Tiempo**: 15 minutos

---

### 04 - Load Balancer

**Qué aprenderás**:
- Crear Load Balancer completo
- Configurar SSL
- Conectar Cloud Run a Load Balancer
- Esperar por certificados SSL

**Recursos creados**:
- IP estática
- Certificado SSL administrado
- Backend service
- URL map
- HTTPS proxy
- Forwarding rule

**Tiempo**: 30 minutos (incluye espera de certificado)

---

## 💡 Tips

### Tip 1: Leer el State

```bash
# Ver todos los recursos
terraform state list

# Ver detalles de un recurso
terraform state show google_secret_manager_secret.example
```

### Tip 2: Formatear Código

```bash
# Formatear automáticamente
terraform fmt
```

### Tip 3: Validar Sintaxis

```bash
# Validar sin conectar a GCP
terraform validate
```

### Tip 4: Ver Plan sin Aplicar

```bash
# Guardar plan en archivo
terraform plan -out=plan.tfplan

# Ver el plan guardado
terraform show plan.tfplan

# Aplicar el plan guardado (sin preguntar)
terraform apply plan.tfplan
```

### Tip 5: Refresh State

```bash
# Actualizar state sin modificar recursos
terraform refresh
```

## ⚠️ Importante

- **Proyecto GCP**: Todos los ejemplos necesitan un proyecto GCP válido
- **Costos**: Estos recursos pueden generar costos mínimos
- **Limpieza**: Recuerda ejecutar `terraform destroy` después de experimentar
- **State local**: Estos ejemplos usan state local (terraform.tfstate)

## 🔗 Siguientes Pasos

Una vez que domines estos ejemplos:

1. ✅ Revisa los módulos en `../../modules/`
2. ✅ Estudia las configuraciones de ambiente en `../../environments/`
3. ✅ Lee el README principal en `../../README.md`
4. ✅ Lee el instructivo completo en `../../INSTRUCTIVO.md`

---

**Happy Learning! 🚀**
