"""
Debug script para testar WhatsApp Connection + ConnectionPool + Status Checker.

Uso:
    python scripts/debug_whatsapp_connection.py <CONNECTION_UUID>

O que faz:
    1. Conecta ao banco e pega a WhatsAppConnection pelo UUID
    2. Usa ConnectionPool para abrir WhatsApp Web (persistent session)
    3. Checa status do DOM (qr_needed, connecting, connected, error)
    4. Mantém aba aberta por 5 minutos para você:
       - Escanear QR
       - Ver status mudar para 'connected'
    5. Fecha sessão gracefully

Perfeito para validar:
    - ConnectionPool funciona
    - status_checker detecta corretamente
    - Session persiste após escanear QR
    - ZERO risco de quebrar Worker
"""
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Adicionar diretório pai ao path para imports funcionarem
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from services.whatsapp.connection_pool import ConnectionPool
from services.whatsapp.status_checker import check_connection_status
from core.database import AsyncSessionLocal
from models.whatsapp_connection import WhatsAppConnection


async def main(connection_id_str: str):
    """
    Debug main function.
    
    Args:
        connection_id_str: UUID da WhatsAppConnection (string)
    """
    try:
        conn_id = UUID(connection_id_str)
    except ValueError:
        print(f"[ERROR] Invalid UUID format: {connection_id_str}")
        print("Exemplo: python scripts/debug_whatsapp_connection.py 8b1d2c0a-1234-5678-90ab-cdef12345678")
        return

    print("=" * 60)
    print("DEBUG: WhatsApp Connection + ConnectionPool + Status Checker")
    print("=" * 60)
    print()

    # Iniciar ConnectionPool / Playwright
    pool = ConnectionPool()
    await pool.start()
    print("[✓] ConnectionPool initialized")
    print()

    async with AsyncSessionLocal() as db:
        # Buscar conexão no banco
        result = await db.execute(
            select(WhatsAppConnection).where(WhatsAppConnection.id == conn_id)
        )
        conn = result.scalars().first()

        if not conn:
            print(f"[ERROR] Connection not found: {conn_id}")
            print()
            print("Dica: Rode este comando para listar conexões:")
            print("  docker-compose exec backend python -c \"")
            print("  from core.database import AsyncSessionLocal")
            print("  from models.whatsapp_connection import WhatsAppConnection")
            print("  from sqlalchemy import select")
            print("  import asyncio")
            print("  async def list_conns():")
            print("      async with AsyncSessionLocal() as db:")
            print("          result = await db.execute(select(WhatsAppConnection))")
            print("          for c in result.scalars().all():")
            print("              print(f'{c.id} - {c.nickname} ({c.status})')")
            print("  asyncio.run(list_conns())")
            print('  "')
            await pool.close_all()
            return

        print(f"[DEBUG] Connection Found:")
        print(f"  - ID: {conn.id}")
        print(f"  - Nickname: {conn.nickname}")
        print(f"  - Status (DB): {conn.status}")
        print(f"  - User ID: {conn.user_id}")
        print()

        # Garantir sessão Playwright (cria ou recupera)
        print("[INFO] Ensuring Playwright session...")
        print("  (Isso pode demorar 10-30s se for a primeira vez)")
        
        context = await pool.get_or_create(str(conn.id))
        
        if not context or not context.pages or len(context.pages) == 0:
            print("[ERROR] Failed to get page from context")
            await pool.close_all()
            return
        
        page = context.pages[0]
        print("[✓] Page obtained from context")
        print(f"  URL: {page.url}")
        print()

        # Checar status do DOM
        print("[INFO] Checking DOM status...")
        status = await check_connection_status(page)
        
        status_emoji = {
            "qr_needed": "📱 QR",
            "connecting": "⏳ Conectando",
            "connected": "✅ Conectado",
            "error": "❌ Erro"
        }
        
        print(f"[DEBUG] DOM Status: {status_emoji.get(status, status)} ({status})")
        print()

        # Instruções baseadas no status
        if status == "qr_needed":
            print("=" * 60)
            print("🔍 QR CODE NECESSÁRIO")
            print("=" * 60)
            print()
            print("Próximos passos:")
            print("  1. Abra a aplicação frontend (se tiver)")
            print("  2. Ou rode este comando para pegar QR da API:")
            print(f"     curl http://localhost:8000/api/v1/connections/{conn.id}/qr")
            print("  3. Escaneie o QR no celular")
            print("  4. Este script vai continuar rodando por 5 minutos")
            print("  5. Você pode rodar novamente depois para ver status 'connected'")
            print()
            print("[INFO] Mantendo aba aberta por 5 minutos...")
            print("       (aguardando você escanear o QR)")
            
        elif status == "connecting":
            print("=" * 60)
            print("⏳ CONECTANDO")
            print("=" * 60)
            print()
            print("WhatsApp está carregando a interface.")
            print("Aguardando 5 minutos para completar conexão...")
            print()
            
        elif status == "connected":
            print("=" * 60)
            print("✅ CONECTADO COM SUCESSO!")
            print("=" * 60)
            print()
            print("WhatsApp Web está totalmente carregado e funcionando.")
            print()
            print("Próximos passos possíveis:")
            print("  1. Testar Group Discovery")
            print("  2. Integrar status_check_cycle no Worker")
            print("  3. Validar que sessão persiste após restart")
            print()
            print("[INFO] Mantendo aba aberta por 5 minutos...")
            print("       (para você validar visualmente se quiser)")
            
        else:  # error
            print("=" * 60)
            print("❌ ERRO DETECTADO")
            print("=" * 60)
            print()
            print("Não foi possível determinar estado do WhatsApp Web.")
            print("Possíveis causas:")
            print("  - Seletores DOM mudaram")
            print("  - Página ainda carregando")
            print("  - Erro de rede")
            print()
            print("[INFO] Mantendo aba aberta por 2 minutos para debug...")

        # Verificar status periodicamente
        check_interval = 10  # segundos
        total_wait = 300 if status != "error" else 120  # 5min ou 2min
        checks = total_wait // check_interval
        
        print()
        print(f"Fazendo {checks} verificações a cada {check_interval}s...")
        print("(pressione Ctrl+C para cancelar)")
        print()
        
        try:
            for i in range(checks):
                await asyncio.sleep(check_interval)
                
                # Re-checar status
                new_status = await check_connection_status(page)
                
                if new_status != status:
                    print(f"[{i+1}/{checks}] Status mudou: {status} → {new_status} {status_emoji.get(new_status, '')}")
                    status = new_status
                    
                    # Se conectou, salvar no banco
                    if new_status == "connected" and conn.status != "connected":
                        conn.status = "connected"
                        conn.updated_at = asyncio.get_event_loop().time()
                        await db.commit()
                        print("           [✓] Status atualizado no banco!")
                else:
                    print(f"[{i+1}/{checks}] Status: {status} (sem mudança)")
        
        except KeyboardInterrupt:
            print()
            print("[INFO] Interrompido pelo usuário (Ctrl+C)")
        
        finally:
            print()
            print("[INFO] Fechando sessão...")
            
            # Salvar estado antes de fechar (opcional)
            try:
                await pool.save_storage_state(str(conn.id))
                print("[✓] Storage state salvo")
            except Exception as e:
                print(f"[!] Não foi possível salvar storage_state: {e}")
            
            await pool.close_all()
            print("[✓] ConnectionPool fechado")
    
    print()
    print("=" * 60)
    print("DEBUG COMPLETO")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/debug_whatsapp_connection.py <CONNECTION_UUID>")
        print()
        print("Exemplo:")
        print("  python scripts/debug_whatsapp_connection.py 8b1d2c0a-1234-5678-90ab-cdef12345678")
        print()
        print("Para listar conexões existentes, rode:")
        print("  docker-compose exec backend python -c \"")
        print("  from core.database import AsyncSessionLocal;")
        print("  from models.whatsapp_connection import WhatsAppConnection;")
        print("  from sqlalchemy import select;")
        print("  import asyncio;")
        print("  async def f():")
        print("      async with AsyncSessionLocal() as db:")
        print("          r = await db.execute(select(WhatsAppConnection));")
        print("          for c in r.scalars():")
        print("              print(f'{c.id} | {c.nickname} | {c.status}');")
        print("  asyncio.run(f())")
        print('  "')
        sys.exit(1)

    asyncio.run(main(sys.argv[1]))
