# Run voice commander with output logged to file
$logFile = "logs\console.log"
if (!(Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }

Write-Host "Voice Commander - output logging to $logFile"
Write-Host "Press Ctrl+C to stop"

& .venv\Scripts\python -m voice_commander.main 2>&1 | Tee-Object -FilePath $logFile
