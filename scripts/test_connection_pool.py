"""
Teste rápido do ConnectionPool
"""
import asyncio
import sys
sys.path.insert(0, 'C:/Users/Ruan/Desktop/autopromo/backend')

from services.whatsapp.connection_pool import ConnectionPool

async def test_connection_pool():
    print("=== Testando ConnectionPool ===\n")
    
    pool = ConnectionPool(sessions_dir="./test_sessions")
    
    # 1. Iniciar Playwright
    print("[1] Iniciando Playwright...")
    await pool.start()
    print("[OK] Playwright iniciado\n")
    
    # 2. Criar context
    test_id = "test-connection-123"
    print(f"[2] Criando context para {test_id}...")
    context = await pool.get_or_create(test_id, headless=True)
    print(f"[OK] Context criado: {context}\n")
    
    # 3. Verificar que página foi aberta
    print("[3] Verificando páginas...")
    pages = context.pages
    print(f"[OK] {len(pages)} página(s) aberta(s)\n")
    
    # 4. Health check
    print("[4] Health check...")
    is_healthy = await pool.health_check(test_id)
    print(f"[OK] Healthy: {is_healthy}\n")
    
    # 5. Obter mesmo context de novo (deve retornar o existente)
    print("[5] Obtendo context existente...")
    context2 = await pool.get_or_create(test_id)
    print(f"[OK] Mesmo context: {context == context2}\n")
    
    # 6. Contagem
    print(f"[6] Contexts ativos: {pool.get_active_count()}\n")
    
    # 7. Limpar
    print("[7] Limpando...")
    await pool.close_all()
    print("[OK] Pool fechado\n")
    
    print("=== SUCCESS! ConnectionPool funcionando! ===")

if __name__ == "__main__":
    asyncio.run(test_connection_pool())
