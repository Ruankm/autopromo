# Script para visualizar QR Code do WhatsApp
# Execute este script após fazer a chamada à API

# Cole o resultado da variável $qr aqui se já tiver executado a API
# OU execute o script completo abaixo

# ============================================
# OPÇÃO 1: Se já tem $qr e $conn nas variáveis
# ============================================

if ($qr -and $conn) {
    Write-Host "✅ Usando QR Code já gerado..." -ForegroundColor Green
} else {
    Write-Host "⚠️  Gerando novo QR Code..." -ForegroundColor Yellow
    
    # Registrar usuário
    $registerBody = @{
        username = "teste_qr_visual@autopromo.com"
        email = "teste_qr_visual@autopromo.com"
        password = "senha123"
        full_name = "Teste QR Visual"
    } | ConvertTo-Json

    try {
        $register = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/register" -Method POST -Body $registerBody -ContentType "application/json"
    } catch {
        # Usuário já existe, tudo bem
    }

    # Login
    $loginBody = "username=teste_qr_visual@autopromo.com&password=senha123"
    $login = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/login" -Method POST -Body $loginBody -ContentType "application/x-www-form-urlencoded"

    # Headers
    $headers = @{ 
        "Authorization" = "Bearer $($login.access_token)"
        "Content-Type" = "application/json" 
    }

    # Criar Conexão
    $connBody = @{
        nickname = "QR Visual Test"
        source_groups = @(@{ name = "Grupo Fonte" })
        destination_groups = @(@{ name = "Grupo Destino" })
    } | ConvertTo-Json

    $conn = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/connections" -Method POST -Headers $headers -Body $connBody

    Write-Host "✅ Conexão criada: $($conn.id)" -ForegroundColor Green

    # GERAR QR CODE
    $qr = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/connections/$($conn.id)/qr" -Headers $headers
    
    Write-Host "✅ QR Code obtido!" -ForegroundColor Green
}

# ============================================
# Criar HTML para visualizar
# ============================================

$htmlPath = "$env:USERPROFILE\Desktop\whatsapp_qrcode.html"

$htmlContent = @"
<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <title>WhatsApp QR Code - AutoPromo</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 600px;
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .success {
            color: #10b981;
            font-size: 20px;
            font-weight: bold;
            margin: 20px 0;
        }
        .qr-box {
            margin: 30px 0;
            padding: 30px;
            background: linear-gradient(145deg, #f9fafb, #e5e7eb);
            border-radius: 15px;
            box-shadow: inset 0 2px 10px rgba(0,0,0,0.1);
        }
        img {
            max-width: 100%;
            height: auto;
            border: 4px solid #667eea;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .instructions {
            background: #f3f4f6;
            padding: 20px;
            border-radius: 10px;
            text-align: left;
            margin-top: 20px;
        }
        .instructions h3 {
            color: #4b5563;
            margin-top: 0;
        }
        .instructions ol {
            color: #6b7280;
            line-height: 1.8;
        }
        .connection-info {
            background: #1f2937;
            color: #10b981;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            margin-top: 20px;
            word-break: break-all;
        }
        .status {
            display: inline-block;
            padding: 8px 16px;
            background: #10b981;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class='container'>
        <h1>📱 WhatsApp QR Code</h1>
        <div class='status'>✅ Gerado via Docker Linux</div>
        <p class='success'>Escaneie para conectar!</p>
        
        <div class='qr-box'>
            <img src='data:image/png;base64,$($qr.qr_code)' alt='QR Code WhatsApp' />
        </div>
        
        <div class='instructions'>
            <h3>📋 Como Escanear:</h3>
            <ol>
                <li>Abra o <strong>WhatsApp</strong> no seu celular</li>
                <li>No Android: <strong>⋮ → Aparelhos conectados</strong></li>
                <li>No iPhone: <strong>Ajustes → Aparelhos conectados</strong></li>
                <li>Toque em <strong>"Conectar um aparelho"</strong></li>
                <li><strong>Escaneie este QR Code</strong></li>
            </ol>
        </div>
        
        <div class='connection-info'>
            <strong>Connection ID:</strong><br>
            $($conn.id)<br><br>
            <strong>Status:</strong> $($qr.status)
        </div>
    </div>
</body>
</html>
"@

# Salvar HTML
$htmlContent | Out-File -FilePath $htmlPath -Encoding UTF8

# Abrir no navegador
Start-Process $htmlPath

Write-Host ""
Write-Host "🎉 QR Code aberto no navegador!" -ForegroundColor Green
Write-Host "📁 Arquivo salvo em: $htmlPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Connection ID: $($conn.id)" -ForegroundColor Yellow
Write-Host "Status: $($qr.status)" -ForegroundColor Yellow
