# Voice Commander - Setup

## 1. Crear venv e instalar dependencias

```powershell
cd C:\dev\my-adventures\voice-commander
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Descargar modelo de Ollama

```powershell
ollama pull qwen2.5-coder:14b-instruct
```

## 3. Ejecutar

```powershell
python -m voice_commander.main
```

## 4. Fix Bash tool (si EINVAL persiste)

El Bash tool de Claude Code no puede crear archivos en `%TEMP%\claude`. Para arreglar:

```powershell
# Borrar el directorio temp corrupto y reiniciar Claude Code
Remove-Item -Recurse -Force "$env:TEMP\claude"
```

Luego reiniciar Claude Code.
