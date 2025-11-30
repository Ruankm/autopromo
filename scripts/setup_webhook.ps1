# Configurar webhook Evolution API v2.3.6
$EVOLUTION_URL = "http://localhost:8081"
$API_KEY = "f708f2fc-471f-4511-83c3-701229e766d5"
$INSTANCE = "ruan"
$BACKEND_URL = "http://host.docker.internal:8000/api/v1/webhook/whatsapp"

Write-Host "=" -NoNewline; 1..70 | % { Write-Host "=" -NoNewline }; Write-Host ""
Write-Host "CONFIGURANDO WEBHOOK - Evolution API v2.3.6"
Write-Host "=" -NoNewline; 1..70 | % { Write-Host "=" -NoNewline }; Write-Host ""
Write-Host "Instancia: $INSTANCE"
Write-Host "Backend: $BACKEND_URL"
Write-Host ""

# Payload correto para v2.3.6
$body = @{
    webhook = @{
        url = $BACKEND_URL
        enabled = $true
        webhookByEvents = $true
        events = @("MESSAGES_UPSERT")
    }
} | ConvertTo-Json -Depth 3

$headers = @{
    "apikey" = $API_KEY
    "Content-Type" = "application/json"
}

try {
    Write-Host "Enviando configuracao..."
    $response = Invoke-RestMethod -Uri "$EVOLUTION_URL/webhook/set/$INSTANCE" -Method Post -Body $body -Headers $headers
    Write-Host "OK Webhook configurado!" -ForegroundColor Green
    Write-Host ""
    
    # Verificar
    Write-Host "Verificando configuracao..."
    $check = Invoke-RestMethod -Uri "$EVOLUTION_URL/webhook/find/$INSTANCE" -Headers $headers
    
    if ($check) {
        Write-Host "OK Webhook ativo!" -ForegroundColor Green
        Write-Host "URL: $($check.webhook.url)"
        Write-Host ""
    }
    
    Write-Host "=" -NoNewline; 1..70 | % { Write-Host "=" -NoNewline }; Write-Host ""
    Write-Host "PRONTO PARA TESTE!"
    Write-Host "=" -NoNewline; 1..70 | % { Write-Host "=" -NoNewline }; Write-Host ""
    Write-Host ""
    Write-Host "Envie mensagem com link no grupo 'Escorrega o Preco'"
    Write-Host "Veja chegar no 'Autopromo' monetizada com tag=autopromo0b-20"
    
} catch {
    Write-Host "ERRO: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Response: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
}
