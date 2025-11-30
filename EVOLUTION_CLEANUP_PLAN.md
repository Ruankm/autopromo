# Evolution API Cleanup Plan

## Arquivos para DELETAR completamente:

1. **backend/services/providers/whatsapp_evolution.py** - Cliente Evolution API (substituído por Playwright)
2. **backend/scripts/setup_evolution_instance.py** - Setup Evolution (não precisa mais)
3. **backend/scripts/test_evolution_debug.py** - Teste Evolution
4. **backend/fix_critical_bugs.py** - Script de correção antigo
5. **docker-compose.evolution.yml** - Docker Evolution API

## Arquivos para ATUALIZAR:

1. **backend/services/providers/__init__.py** - Remover imports Evolution
2. **backend/workers/dispatcher.py** - Atualizar para usar PlaywrightGateway
3. **backend/services/mirror_service.py** - Remover referências Evolution
4. **backend/schemas/whatsapp.py** - Atualizar schemas
5. **backend/models/whatsapp_instance.py** - Deprecar ou remover
6. **backend/models/group.py** - Remover campos Evolution
7. **backend/main.py** - Remover checks Evolution
8. **backend/.env.example** - Remover variáveis Evolution

## Models para DEPRECAR:

- `WhatsAppInstance` (substituído por `WhatsAppConnection`)
- Campos Evolution em `GroupSource` e `GroupDestination`

## Executar limpeza em ordem:

1. Delete arquivos obsoletos
2. Update imports e dependencies
3. Update models (marcar como deprecated)
4. Update services
5. Commit changes

---

**Ação:** DELETE + UPDATE para remover 100% das referências Evolution API
