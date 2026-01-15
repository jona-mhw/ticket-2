# 🔧 Ejecutar Claude Code en PC Corporativo (SSL Fix)

## El Problema
Error: `SELF_SIGNED_CERT_IN_CHAIN`
- La red corporativa tiene un proxy que intercepta HTTPS
- Node.js no confía en el certificado corporativo

---

## ✅ Solución Paso a Paso

### 1. Configurar npm para ignorar SSL
```powershell
npm config set strict-ssl false
```

### 2. Agregar variable de entorno al perfil de PowerShell
```powershell
notepad $PROFILE
```
Agregar esta línea al archivo:
```powershell
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
```

### 3. (Re)instalar Claude Code
```powershell
# Desinstalar versión anterior
npm uninstall -g @anthropic-ai/claude-code

# Limpiar caché
npm cache clean --force

# Eliminar instalación manual (si existe)
Remove-Item -Recurse -Force "$env:APPDATA\npm\node_modules\@anthropic-ai" -ErrorAction SilentlyContinue
Remove-Item -Force "$env:APPDATA\npm\claude*" -ErrorAction SilentlyContinue

# Instalar última versión
npm install -g @anthropic-ai/claude-code@latest
```

### 4. Ejecutar Claude Code
```powershell
claude --dangerously-skip-permissions
```

---

## 📋 Comando Rápido (Todo en Uno)
```powershell
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"; claude --dangerously-skip-permissions
```

---

## ⚠️ Notas Importantes
- `NODE_TLS_REJECT_UNAUTHORIZED = "0"` desactiva verificación SSL
- Es "seguro" en red corporativa porque el proxy ya inspecciona todo
- Para solución permanente: pedir certificado raíz corporativo a TI

---

## 📅 Probado
- Fecha: 13 Enero 2026
- Versión: Claude Code 2.1.7
- PC: Windows (Red Corporativa RedSalud)
