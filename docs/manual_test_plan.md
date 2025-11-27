# Plano de Testes Manual - AutoPromo Cloud

Este documento descreve os passos para verificar manualmente o funcionamento do sistema AutoPromo Cloud, cobrindo desde o setup inicial até o fluxo completo de processamento de ofertas.

## 1. Pré-requisitos

Antes de iniciar, certifique-se de que o ambiente está rodando.

### Backend
1.  **Banco de Dados e Redis**:
    ```bash
    docker compose up -d postgres redis
    ```
2.  **Migrações**:
    ```bash
    cd backend
    uv run alembic upgrade head
    ```
3.  **Servidor API**:
    ```bash
    uv run uvicorn main:app --reload
    ```

### Frontend
1.  **Dependências**:
    ```bash
    cd frontend
    npm install
    ```
2.  **Servidor de Desenvolvimento**:
    ```bash
    npm run dev
    ```
    Acesse: `http://localhost:3000`

---

## 2. Fluxos Críticos

### 2.1. Registro e Login

**Objetivo**: Verificar se a autenticação JWT está funcionando.

1.  Acesse `http://localhost:3000/register`.
2.  Preencha:
    *   Nome: `Teste User`
    *   Email: `teste@autopromo.com`
    *   Senha: `password123`
3.  Clique em "Registrar".
4.  **Esperado**: Redirecionamento para `/login` (ou login automático).
5.  Acesse `http://localhost:3000/login`.
6.  Faça login com as credenciais criadas.
7.  **Esperado**: Redirecionamento para `/dashboard`. Cookie `autopromo_token` deve estar presente.

### 2.2. Configuração Inicial

**Objetivo**: Popular o banco com dados necessários para o processamento.

1.  **Tags de Afiliado**:
    *   Vá para `/dashboard/tags`.
    *   Adicione:
        *   Loja: `Amazon`
        *   Tag: `minhatag-20`
    *   **Esperado**: Tag aparece na tabela.
2.  **Grupos**:
    *   Vá para `/dashboard/groups`.
    *   Aba "Grupos Fonte": Adicione um grupo WhatsApp (ex: `120363025@g.us`).
    *   Aba "Grupos Destino": Adicione um grupo Telegram (ex: `-100123456`).
    *   **Esperado**: Grupos aparecem nas respectivas tabelas.
3.  **Configurações**:
    *   Vá para `/dashboard/settings`.
    *   Defina Janela: `00:00` às `23:59` (para facilitar testes).
    *   Salve.
    *   **Esperado**: Toast/Alert de sucesso.

### 2.3. Recebimento de Oferta (Webhook)

**Objetivo**: Simular a chegada de uma mensagem do WhatsApp.

1.  Use Postman ou cURL para enviar para `http://localhost:8000/api/v1/webhook/whatsapp`.
2.  **Headers**:
    *   `X-User-ID`: (Pegue o ID do usuário no banco ou logs do backend, se necessário implemente log no endpoint de webhook para ver o user resolvido, ou use um user_id fixo se tiver mapeamento estático). *Nota: O sistema atual resolve user por mapeamento na Evolution API. Para teste local, certifique-se de que o webhook logic consegue identificar o usuário.*
3.  **Body**:
    ```json
    {
      "event": "messages.upsert",
      "instance": "test_instance",
      "data": {
        "key": { "remoteJid": "120363025@g.us", "fromMe": false, "id": "MSG123" },
        "message": { "conversation": "Oferta teste https://amzn.to/exemplo" },
        "messageTimestamp": 1700000000,
        "pushName": "Tester"
      }
    }
    ```
4.  **Esperado**:
    *   Backend log: `Ingestion successful`.
    *   Redis: Chave `queue:ingestion` deve ter um item.

### 2.4. Processamento (Worker)

**Objetivo**: Verificar se o worker processa a fila.

1.  Em outro terminal:
    ```bash
    cd backend
    uv run python -m workers.worker
    ```
2.  **Esperado**:
    *   Log: `Processing message...`
    *   Log: `Offer processed successfully`.
    *   Dashboard (`/dashboard`): "Total na Fila" ou "Enviados Hoje" deve mudar (dependendo do status final). Tabela "Últimas Ofertas" deve mostrar a oferta.

### 2.5. Dispatcher

**Objetivo**: Verificar envio para o destino.

1.  Em outro terminal:
    ```bash
    cd backend
    uv run python -m workers.dispatcher
    ```
2.  **Esperado**:
    *   Log: `Dispatching offer...`
    *   Log: `Sent to provider...` (se configurado mock ou real).

---

## 3. Cenários de Erro

1.  **Webhook Inválido**: Enviar JSON quebrado. Esperado: 422 Unprocessable Entity.
2.  **Duplicidade**: Enviar o mesmo webhook 2x. Esperado: Segundo envio retorna status `duplicate`.
3.  **Login Falho**: Senha errada. Esperado: Erro na UI do frontend.
