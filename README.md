# Voice Commander

Pipeline local **voz -> accion** para Windows. Habla en espanol (o ingles, o mezclado) y obtiene comandos de terminal o texto transcrito.

```
  voz  ->  Whisper STT  ->  Ollama LLM  ->  comando PowerShell
  voz  ->  Whisper STT  ->  clipboard (para pegar en Claude Code, etc.)
```

## Quickstart

```powershell
# 1. Setup
cd C:\dev\my-adventures\voice-commander
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. Ollama (si no lo tienes)
# Descargar desde https://ollama.com/download
ollama pull qwen2.5-coder:14b-instruct

# 3. Ejecutar
.\run.ps1
# o directamente:
python -m voice_commander.main
```

Shortcut de PowerShell: `voice-commander` (abre en nueva terminal).

## Uso

| Hotkey | Modo | Que hace |
|--------|------|----------|
| `Ctrl+Alt+V` | Comando | Graba voz -> transcribe -> genera comando -> menu interactivo |
| `Ctrl+Alt+T` | Texto | Graba voz -> transcribe -> copia al clipboard |
| `Ctrl+C` | — | Salir |

**Push-to-talk**: manten presionado el hotkey mientras hablas, suelta cuando termines.

### Modo Comando

Despues de generar el comando, el menu ofrece:

```
  e ejecutar    Corre el comando en PowerShell 7
  c copiar      Copia al clipboard
  r editar      Permite modificar el comando antes de ejecutar
  x cancelar    Descarta
```

### Modo Texto

Transcribe y copia automaticamente al clipboard. Ideal para dictar a Claude Code, chat, o cualquier editor.

## Arquitectura

```
voice_commander/
  config.py        Configuracion (hotkeys, modelos, Ollama URL, vocabulario)
  recorder.py      Captura de audio con sounddevice + hotkeys globales
  transcriber.py   faster-whisper wrapper (medium, CUDA, float16)
  commander.py     Ollama REST API (qwen2.5-coder:14b-instruct)
  executor.py      subprocess runner (pwsh, timeout 30s)
  logger.py        JSONL logging para dataset
  main.py          Orquestador + CLI UI
```

```
Hotkey -> Recorder -> Whisper STT -> [Ollama LLM] -> CLI menu -> Executor
                                     (solo comando)              (solo comando)
                                  -> Clipboard
                                     (solo texto)
```

## Modelos

| Componente | Modelo | Por que |
|------------|--------|---------|
| STT | `faster-whisper medium` | Mejor relacion accuracy/speed para code-switching es/en. ~1.5GB VRAM |
| LLM | `qwen2.5-coder:14b-instruct` | 89% HumanEval, excelente en shell/PowerShell, variante instruct confiable |

Whisper usa un `initial_prompt` con vocabulario custom (KAPS, Syion, Komoco, etc.) para mejorar reconocimiento de terminos tecnicos y nombres propios.

## Configuracion

Los defaults estan en `config.py`. Para override, crear `config.json` en la raiz:

```json
{
  "whisper_model": "large-v3",
  "ollama_model": "qwen2.5-coder:7b-instruct",
  "exec_timeout": 60
}
```

El system prompt de Ollama conoce los shortcuts del `$PROFILE` de PowerShell (go-kaps, agent-sales, etc.) para que puedas decir "ve a kaps" y genere `go-kaps`.

## Logging

Cada interaccion se loguea en `logs/interactions.jsonl`:

```json
{
  "id": "uuid",
  "timestamp": "ISO-8601",
  "mode": "command",
  "transcription": "muestra los ultimos commits",
  "generated_command": "git log --oneline -5",
  "user_action": "executed",
  "execution_exit_code": 0,
  "latency_stt_ms": 480,
  "latency_llm_ms": 2400
}
```

Rotacion automatica a 50MB. Util para evaluar calidad del STT y fine-tuning futuro.

## Stack

- **faster-whisper** — STT, 4x mas rapido que openai-whisper, CTranslate2
- **sounddevice** — Captura de audio (PortAudio)
- **keyboard** — Hotkeys globales en Windows
- **Ollama** — LLM local via REST API
- **pyperclip** — Clipboard
- **colorama** — Colores en terminal

## Requisitos

- Python 3.10+
- NVIDIA GPU con CUDA (para faster-whisper en GPU)
- Ollama corriendo (`ollama serve`)
- Windows 11 (hotkeys globales via `keyboard` library)
