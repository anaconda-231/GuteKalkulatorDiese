# Startet den Konfigurator und veroeffentlicht ihn ueber einen Cloudflare
# Quick Tunnel, damit Kollegen ihn per Link im Browser oeffnen koennen.
#
#   .\start_tunnel.ps1
#
# Zum Beenden das Fenster schliessen oder Strg+C - danach ist der Link sofort
# tot. Die URL ist bei jedem Start eine andere (Quick Tunnel ohne Cloudflare-
# Account); fuer eine feste Adresse braucht es einen benannten Tunnel und
# damit einen Cloudflare-Account.
#
# Der Flask-Server laeuft bewusst OHNE debug (siehe server.py): der Werkzeug-
# Debugger wuerde bei jedem Fehler eine interaktive Python-Konsole anbieten,
# die ueber den oeffentlichen Link fuer jeden erreichbar waere.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$port = 5000
$env:KONFIGURATOR_HOST = "127.0.0.1"
$env:KONFIGURATOR_PORT = "$port"
Remove-Item Env:\KONFIGURATOR_DEBUG -ErrorAction SilentlyContinue

if (-not (Test-Path ".\cloudflared.exe")) {
    Write-Host "cloudflared.exe fehlt - wird heruntergeladen ..."
    Invoke-WebRequest -UseBasicParsing `
        -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" `
        -OutFile ".\cloudflared.exe"
}

Write-Host "Starte Konfigurator auf http://127.0.0.1:$port ..."
$server = Start-Process -FilePath "python" -ArgumentList "server.py" `
    -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru

# Warten, bis Flask wirklich Anfragen annimmt - sonst startet der Tunnel
# schneller als der Server und die erste Anfrage laeuft ins Leere.
$ready = $false
foreach ($i in 1..30) {
    Start-Sleep -Milliseconds 500
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:$port/" -UseBasicParsing -TimeoutSec 3 | Out-Null
        $ready = $true
        break
    } catch { }
}
if (-not $ready) {
    Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    throw "Server ist nicht gestartet - bitte 'python server.py' manuell pruefen."
}

$log = Join-Path $PSScriptRoot "cloudflared.log"
Remove-Item $log -ErrorAction SilentlyContinue
$tunnel = Start-Process -FilePath ".\cloudflared.exe" `
    -ArgumentList "tunnel","--url","http://127.0.0.1:$port","--logfile",$log,"--loglevel","info" `
    -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru

$url = $null
foreach ($i in 1..60) {
    Start-Sleep -Milliseconds 500
    if (Test-Path $log) {
        $hit = Select-String -Path $log -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -AllMatches
        if ($hit) { $url = $hit.Matches[0].Value; break }
    }
}

if ($url) {
    Write-Host ""
    Write-Host "  Link fuer Kollegen:  $url" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Solange dieses Fenster offen bleibt, ist der Link erreichbar."
    Write-Host "  Strg+C beendet Tunnel und Server."
} else {
    Write-Host "Tunnel-URL nicht gefunden - siehe $log" -ForegroundColor Yellow
}

try {
    Wait-Process -Id $tunnel.Id
} finally {
    Stop-Process -Id $tunnel.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Tunnel und Server beendet."
}
