# 💻 Instructivo: GitHub Copilot + VS Code - Aplicar Cambios Localmente

**Propósito**: Guía para aplicar cambios generados por Claude Code Web en tu entorno local de VS Code usando GitHub Copilot.

**Última actualización**: 2025-01-09
**Versión**: v0.1.4

---

## 📋 Contexto

Cuando Claude Code Web trabaja en issues y pushea cambios a GitHub, necesitas:
1. Traer esos cambios a tu máquina local
2. Validar que todo funciona
3. Opcionalmente hacer ajustes con GitHub Copilot

Este instructivo cubre **dos escenarios**:
- **Escenario A**: Ya tienes el repo clonado y trabajas en él regularmente
- **Escenario B**: Clonas el repo por primera vez

---

## 🎯 Escenario A: Repo Ya Clonado (Actualizar Cambios)

### Paso 1: Verificar Estado Actual

```bash
# Abre terminal en VS Code (Ctrl+` o Cmd+`)
cd /ruta/a/ticket-2

# Ver estado de tu repo local
git status

# Ver branch actual
git branch

# Ver commits recientes
git log --oneline -5
```

**Esperado**:
```
* 9a5e451 (HEAD -> main) fix: actualizar freezegun 1.4.0 → 1.5.5
* 18bf4c1 docs: resumen completo de sesión + nueva issue
* 7b0e5df docs: guía completa de implementación Redis Cache
```

### Paso 2: Traer Cambios del Branch de Claude

Claude trabaja en branches que empiezan con `claude/`. Para traer sus cambios:

```bash
# Opción 1: Fetch solo el branch específico
git fetch origin claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F

# Opción 2: Fetch todos los branches (más lento)
git fetch --all

# Ver branches remotos disponibles
git branch -r

# Ver diferencias antes de hacer checkout
git log main..origin/claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F --oneline
```

### Paso 3: Hacer Checkout del Branch de Claude

```bash
# Checkout del branch remoto
git checkout claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F

# Verificar que estás en el branch correcto
git branch
# Debe mostrar: * claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F

# Ver los archivos modificados
git show --name-only
```

### Paso 4: Revisar Cambios en VS Code

**Archivos modificados recientemente** (ejemplo Issue #8):
```
tests/test_audit_logs.py    (NUEVO - 488 líneas)
requirements.txt            (MODIFICADO - freezegun 1.5.5)
```

**Usa VS Code para revisar**:
1. Panel lateral → Source Control (Ctrl+Shift+G)
2. Revisa archivos marcados como "Changes"
3. Click en archivo → Ve diff lado a lado
4. Usa GitHub Copilot para entender código:
   - Selecciona código → Click derecho → "Copilot: Explain This"

### Paso 5: Configurar Entorno Virtual (Primera Vez)

Si es tu primera vez trabajando localmente:

```bash
# Crear virtualenv
python3 -m venv .venv

# Activar virtualenv
# En macOS/Linux:
source .venv/bin/activate
# En Windows:
.venv\Scripts\activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 6: Actualizar Dependencias

Si `requirements.txt` cambió:

```bash
# Con virtualenv activado
pip install -r requirements.txt --upgrade

# Verificar versión específica (ejemplo freezegun)
pip show freezegun
# Debe mostrar: Version: 1.5.5
```

### Paso 7: Ejecutar Tests Localmente

```bash
# Configurar variables de entorno para testing
export FLASK_ENV=testing
export DATABASE_URL='sqlite:///:memory:'
export SECRET_KEY='test-secret-key'

# Ejecutar todos los tests
python -m pytest tests/ -v

# Esperado: 60/60 tests passed
```

**Si tests fallan**:
```bash
# Ver output detallado
python -m pytest tests/ -v --tb=long

# Ejecutar test específico que falla
python -m pytest tests/test_audit_logs.py::TestLoginAuditMultiTenancy::test_superuser_sees_all_login_logs -v
```

### Paso 8: Hacer Merge a Main (Opcional)

Si todo funciona y quieres mergear localmente:

```bash
# Volver a main
git checkout main

# Mergear branch de Claude
git merge claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F

# Si hay conflictos, VS Code los resaltará
# Usa "Accept Current Change" o "Accept Incoming Change"

# Después del merge
git push origin main
```

**⚠️ IMPORTANTE**: Es preferible hacer merge desde GitHub UI (Pull Request) para mantener historial limpio.

---

## 🆕 Escenario B: Clonar Repo por Primera Vez

### Paso 1: Clonar Repositorio

```bash
# En terminal de VS Code
cd ~/projects  # O donde guardes tus proyectos

# Clonar repo
git clone https://github.com/jona-mhw/ticket-2.git

# Entrar al directorio
cd ticket-2
```

### Paso 2: Abrir en VS Code

```bash
# Desde terminal
code .

# O abre VS Code → File → Open Folder → Selecciona ticket-2/
```

### Paso 3: Instalar Extensiones Recomendadas

En VS Code, instala:
- ✅ **Python** (Microsoft)
- ✅ **GitHub Copilot**
- ✅ **GitHub Copilot Chat**
- ✅ **Pylance** (Microsoft)
- ✅ **GitLens** (opcional, pero útil)

### Paso 4: Configurar Python Interpreter

1. `Cmd/Ctrl + Shift + P` → "Python: Select Interpreter"
2. Selecciona Python 3.11 o superior (preferiblemente 3.13)

### Paso 5: Crear Entorno Virtual

```bash
# Crear virtualenv
python3 -m venv .venv

# Activar
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 6: Configurar PostgreSQL Local (Opcional)

**Para desarrollo con DB real**:

```bash
# macOS (con Homebrew)
brew install postgresql@17
brew services start postgresql@17

# Crear base de datos
createdb ticket_home_dev

# Configurar .env
cp .env.example .env  # Si existe
# O crea .env manualmente:
cat > .env << EOF
DATABASE_URL=postgresql://localhost/ticket_home_dev
SECRET_KEY=dev-secret-key
FLASK_ENV=development
ENABLE_IAP=false
ENABLE_DEMO_LOGIN=true
EOF
```

**Para testing (sin DB real)**:
```bash
# No se necesita PostgreSQL
# Los tests usan SQLite en memoria automáticamente
```

### Paso 7: Ejecutar Migraciones

```bash
# Con virtualenv activado
flask db upgrade

# Seed data de prueba (opcional)
flask seed
```

### Paso 8: Ejecutar Tests

```bash
# Todos los tests
python -m pytest tests/ -v

# Con coverage
python -m pytest tests/ --cov=. --cov-report=html

# Abrir reporte HTML
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## 🔄 Flujo de Trabajo Típico

### Cuando Claude Pushea Cambios Nuevos

1. **Recibe notificación** (email de GitHub o revisa manualmente)
2. **Fetch cambios**:
   ```bash
   git fetch origin claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F
   ```
3. **Ver qué cambió**:
   ```bash
   git log main..origin/claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F --oneline
   git diff main origin/claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F
   ```
4. **Checkout del branch**:
   ```bash
   git checkout claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F
   git pull  # Asegurarte de tener lo último
   ```
5. **Actualizar dependencias** (si cambió requirements.txt):
   ```bash
   pip install -r requirements.txt --upgrade
   ```
6. **Ejecutar tests**:
   ```bash
   pytest tests/ -v
   ```
7. **Revisar código** con Copilot (ver sección siguiente)
8. **Hacer ajustes** si es necesario
9. **Mergear a main** (preferiblemente desde GitHub UI)

---

## 🤖 Usar GitHub Copilot Efectivamente

### Para Entender Código Nuevo

**Ejemplo: Entender tests de auditoría**

1. Abre `tests/test_audit_logs.py`
2. Selecciona función `test_superuser_sees_all_login_logs`
3. Click derecho → **"Copilot: Explain This"**

**Prompt en Copilot Chat**:
```
Explica qué hace este test y por qué es importante para multi-tenancy.
```

### Para Hacer Modificaciones

**Ejemplo: Agregar nuevo test**

**Prompt en Copilot Chat**:
```
Basándote en el archivo tests/test_audit_logs.py, crea un nuevo test
llamado test_visualizador_cannot_modify_logs que valide que un usuario
visualizador no puede modificar logs de auditoría.
```

### Para Debugging

**Ejemplo: Test que falla**

**Prompt en Copilot Chat**:
```
Este test está fallando:
[pega el output del test]

¿Cuál puede ser el problema y cómo lo soluciono?
```

### Para Refactoring

**Prompt en Copilot Chat**:
```
Tengo este código [pega código]. Quiero refactorizarlo para:
1. Mejorar legibilidad
2. Seguir el patrón usado en models.py
3. Mantener compatibilidad con SQLAlchemy 3.0.5
```

---

## 🛠️ Scripts Útiles

### Script de Setup Completo (Primera Vez)

Crea `setup_local.sh`:

```bash
#!/bin/bash
# Setup completo del entorno local

echo "🔧 Configurando Ticket Home localmente..."

# Crear virtualenv
python3 -m venv .venv

# Activar virtualenv
source .venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env para testing
cat > .env.test << EOF
FLASK_ENV=testing
DATABASE_URL=sqlite:///:memory:
SECRET_KEY=test-secret-key
ENABLE_IAP=false
ENABLE_DEMO_LOGIN=true
SKIP_AUTH_FOR_TESTING=true
EOF

echo "✅ Setup completo!"
echo "Ejecuta: source .venv/bin/activate"
echo "Luego: pytest tests/ -v"
```

Ejecuta:
```bash
chmod +x setup_local.sh
./setup_local.sh
```

### Script de Update (Traer Cambios de Claude)

Crea `update_from_claude.sh`:

```bash
#!/bin/bash
# Actualizar cambios desde branch de Claude

CLAUDE_BRANCH="claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F"

echo "📥 Trayendo cambios de Claude..."

# Fetch cambios
git fetch origin $CLAUDE_BRANCH

# Mostrar diferencias
echo "📊 Cambios nuevos:"
git log main..origin/$CLAUDE_BRANCH --oneline

# Preguntar si hacer checkout
read -p "¿Hacer checkout de este branch? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    git checkout $CLAUDE_BRANCH
    git pull

    # Actualizar dependencias si cambió requirements.txt
    if git diff HEAD@{1} HEAD --name-only | grep -q "requirements.txt"; then
        echo "📦 Actualizando dependencias..."
        source .venv/bin/activate
        pip install -r requirements.txt --upgrade
    fi

    # Ejecutar tests
    echo "🧪 Ejecutando tests..."
    source .venv/bin/activate
    pytest tests/ -v

    echo "✅ Actualización completa!"
fi
```

Ejecuta:
```bash
chmod +x update_from_claude.sh
./update_from_claude.sh
```

---

## 🧪 Testing Local

### Ejecutar Tests por Categoría

```bash
# Solo tests de FPA (críticos)
pytest -m fpa -v

# Solo tests de autenticación
pytest -m auth -v

# Solo tests unitarios
pytest -m unit -v
```

### Tests con Coverage Específico

```bash
# Coverage de models.py
pytest tests/test_models.py --cov=models --cov-report=term-missing

# Coverage de audit logs
pytest tests/test_audit_logs.py --cov=models --cov-report=html
open htmlcov/index.html
```

### Watch Mode (Ejecutar Tests Automáticamente)

Instala pytest-watch:
```bash
pip install pytest-watch
```

Ejecuta:
```bash
# Re-ejecuta tests cuando archivos cambian
ptw tests/ -- -v
```

---

## 🐛 Troubleshooting Común

### Error: "No module named 'flask'"

**Solución**:
```bash
# Verifica que virtualenv esté activado
which python
# Debe mostrar: /ruta/a/ticket-2/.venv/bin/python

# Si no está activado:
source .venv/bin/activate

# Reinstala dependencias
pip install -r requirements.txt
```

### Error: "freezegun compatibility"

**Solución**:
```bash
# Actualiza freezegun a 1.5.5 (compatible con Python 3.13)
pip install freezegun==1.5.5 --upgrade

# Verifica versión
pip show freezegun
```

### Tests fallan: "database is locked"

**Solución**:
```bash
# Asegúrate de usar SQLite en memoria para tests
export DATABASE_URL='sqlite:///:memory:'
pytest tests/ -v
```

### Git: "Your branch has diverged"

**Solución**:
```bash
# Opción 1: Reset a origin (perder cambios locales)
git reset --hard origin/claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F

# Opción 2: Stash cambios locales
git stash
git pull
git stash pop  # Si quieres recuperar tus cambios
```

### VS Code no reconoce imports

**Solución**:
1. `Cmd/Ctrl + Shift + P`
2. "Python: Select Interpreter"
3. Selecciona `.venv/bin/python`
4. Recarga VS Code si es necesario

---

## 📊 Checklist de Validación Local

Después de traer cambios de Claude, verifica:

- [ ] Virtualenv activado (`which python` → muestra `.venv`)
- [ ] Dependencias actualizadas (`pip list | grep freezegun` → 1.5.5)
- [ ] Tests pasan (`pytest tests/ -v` → 60/60 passed)
- [ ] Coverage aceptable (`pytest --cov` → >90% en models.py)
- [ ] Sin errores de linting (si usas pylint/flake8)
- [ ] Código revisado y entendido (con ayuda de Copilot si es necesario)

---

## 🎓 Tips y Mejores Prácticas

### 1. Usa Git Stash para Cambios Temporales

```bash
# Guardar cambios sin commit
git stash

# Hacer checkout a otro branch
git checkout claude/explore-star-project-011CUw1ni9g5PQUA31kvLn6F

# Recuperar cambios después
git stash pop
```

### 2. Crea Alias para Comandos Frecuentes

Agrega a tu `~/.bashrc` o `~/.zshrc`:

```bash
# Alias para Ticket Home
alias ticket-activate='source ~/projects/ticket-2/.venv/bin/activate'
alias ticket-test='cd ~/projects/ticket-2 && pytest tests/ -v'
alias ticket-update='cd ~/projects/ticket-2 && ./update_from_claude.sh'
```

### 3. Usa GitLens en VS Code

- Ver historial de commits por línea
- Ver quién hizo cada cambio
- Comparar branches visualmente

### 4. Configura Pre-commit Hooks (Opcional)

Crea `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Ejecutar tests antes de cada commit

echo "Ejecutando tests..."
pytest tests/ -v

if [ $? -ne 0 ]; then
    echo "❌ Tests fallaron. Commit abortado."
    exit 1
fi

echo "✅ Tests OK. Continuando con commit..."
```

Activa:
```bash
chmod +x .git/hooks/pre-commit
```

---

## 🔗 Recursos Útiles

### VS Code Extensions

- **Python** (ms-python.python)
- **GitHub Copilot** (GitHub.copilot)
- **GitHub Copilot Chat** (GitHub.copilot-chat)
- **Pylance** (ms-python.vscode-pylance)
- **GitLens** (eamodio.gitlens)
- **Python Test Explorer** (littlefoxteam.vscode-python-test-adapter)

### Keyboard Shortcuts Útiles

| Acción | macOS | Windows/Linux |
|--------|-------|---------------|
| Terminal | `Ctrl + \`` | `Ctrl + \`` |
| Command Palette | `Cmd + Shift + P` | `Ctrl + Shift + P` |
| Source Control | `Cmd + Shift + G` | `Ctrl + Shift + G` |
| Search Files | `Cmd + P` | `Ctrl + P` |
| Search in Files | `Cmd + Shift + F` | `Ctrl + Shift + F` |
| Copilot Inline Suggest | `Option + ]` | `Alt + ]` |
| Copilot Chat | `Cmd + I` | `Ctrl + I` |

---

## 📞 Soporte

Si encuentras problemas:

1. **Revisa logs de tests**: `pytest tests/ -v --tb=long`
2. **Consulta documentación**: `_docs/INSTRUCTIVO_CLAUDE_CODE_WEB.md`
3. **Usa Copilot Chat**: Pega el error y pide explicación
4. **Revisa commits recientes**: `git log --oneline -10`

---

**Última actualización**: 2025-01-09 (v0.1.4)

**Próxima revisión**: Después de Issue #8 merge y release v0.1.4
