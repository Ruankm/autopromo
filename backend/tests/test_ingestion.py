"""
Testes para o serviço de ingestão.

Testa deduplicação, normalização de texto, extração de URLs e enfileiramento.
"""
import pytest
import json
from datetime import datetime

# Mock Redis para testes
class MockRedis:
    def __init__(self):
        self.storage = {}
        self.queues = {}
    
    async def set(self, key, value, ex=None, nx=False):
        """Mock de SET com suporte a NX."""
        if nx and key in self.storage:
            return None  # Já existe
        
        self.storage[key] = value
        return "OK"
    
    async def rpush(self, queue, value):
        """Mock de RPUSH."""
        if queue not in self.queues:
            self.queues[queue] = []
        self.queues[queue].append(value)
        return len(self.queues[queue])
    
    def get_queue(self, queue):
        """Helper para testes - retorna itens da fila."""
        return self.queues.get(queue, [])


# Importar funções do serviço
import sys
sys.path.append('..')
from services.ingestion_service import (
    normalize_text,
    extract_url,
    generate_dedup_hash,
)


class TestNormalization:
    """Testes de normalização de texto."""
    
    def test_normalize_lowercase(self):
        """Texto deve ser convertido para lowercase."""
        text = "OFERTA IMPERDÍVEL! Notebook Gamer"
        result = normalize_text(text)
        assert result == "oferta imperdível! notebook gamer"
    
    def test_normalize_spaces(self):
        """Espaços extras devem ser removidos."""
        text = "Oferta    com    espaços     extras"
        result = normalize_text(text)
        assert result == "oferta com espaços extras"
    
    def test_normalize_emoji_repetition(self):
        """Emojis repetidos devem ser reduzidos."""
        text = "🔥🔥🔥🔥 OFERTA 🔥🔥🔥"
        result = normalize_text(text)
        assert "🔥" in result
        # Deve ter menos emojis repetidos
        assert result.count("🔥") < text.count("🔥")


class TestURLExtraction:
    """Testes de extração de URLs."""
    
    def test_extract_http_url(self):
        """Deve extrair URL HTTP."""
        text = "Confira em http://example.com/produto"
        url = extract_url(text)
        assert url == "http://example.com/produto"
    
    def test_extract_https_url(self):
        """Deve extrair URL HTTPS."""
        text = "Compre agora https://amazon.com.br/dp/B08XYZ"
        url = extract_url(text)
        assert url == "https://amazon.com.br/dp/B08XYZ"
    
    def test_extract_shortened_url(self):
        """Deve extrair URL encurtada."""
        text = "Clique aqui: https://amzn.to/abc123"
        url = extract_url(text)
        assert url == "https://amzn.to/abc123"
    
    def test_no_url(self):
        """Deve retornar None se não houver URL."""
        text = "Oferta sem link"
        url = extract_url(text)
        assert url is None


class TestDedupHash:
    """Testes de geração de hash de deduplicação."""
    
    def test_same_input_same_hash(self):
        """Mesma entrada deve gerar mesmo hash."""
        user_id = "user-123"
        url = "https://example.com/produto"
        text = "oferta incrível"
        
        hash1 = generate_dedup_hash(user_id, url, text)
        hash2 = generate_dedup_hash(user_id, url, text)
        
        assert hash1 == hash2
    
    def test_different_user_different_hash(self):
        """Usuários diferentes devem gerar hashes diferentes."""
        url = "https://example.com/produto"
        text = "oferta incrível"
        
        hash1 = generate_dedup_hash("user-1", url, text)
        hash2 = generate_dedup_hash("user-2", url, text)
        
        assert hash1 != hash2
    
    def test_different_url_different_hash(self):
        """URLs diferentes devem gerar hashes diferentes."""
        user_id = "user-123"
        text = "oferta incrível"
        
        hash1 = generate_dedup_hash(user_id, "https://example.com/p1", text)
        hash2 = generate_dedup_hash(user_id, "https://example.com/p2", text)
        
        assert hash1 != hash2
    
    def test_hash_is_sha256(self):
        """Hash deve ter formato SHA-256 (64 caracteres hex)."""
        hash_result = generate_dedup_hash("user", "http://url.com", "text")
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)


@pytest.mark.asyncio
class TestDeduplication:
    """Testes de deduplicação com mock Redis."""
    
    async def test_first_message_accepted(self):
        """Primeira mensagem deve ser aceita."""
        # TODO: Implementar quando Redis real estiver disponível para testes
        pass
    
    async def test_duplicate_message_rejected(self):
        """Mensagem duplicada deve ser rejeitada."""
        # TODO: Implementar quando Redis real estiver disponível para testes
        pass
    
    async def test_different_user_same_content_accepted(self):
        """Usuários diferentes podem ter mesmo conteúdo."""
        # TODO: Implementar quando Redis real estiver disponível para testes
        pass


if __name__ == "__main__":
    # Executar testes unitários simples
    print("=== Testando Normalização ===")
    test = TestNormalization()
    test.test_normalize_lowercase()
    test.test_normalize_spaces()
    print("✓ Normalização OK")
    
    print("\n=== Testando Extração de URL ===")
    test_url = TestURLExtraction()
    test_url.test_extract_http_url()
    test_url.test_extract_https_url()
    test_url.test_no_url()
    print("✓ Extração de URL OK")
    
    print("\n=== Testando Hash de Deduplicação ===")
    test_hash = TestDedupHash()
    test_hash.test_same_input_same_hash()
    test_hash.test_different_user_different_hash()
    test_hash.test_hash_is_sha256()
    print("✓ Hash de Deduplicação OK")
    
    print("\n✅ Todos os testes unitários passaram!")
