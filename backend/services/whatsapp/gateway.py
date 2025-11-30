"""
WhatsApp Gateway - Interface abstrata para providers WhatsApp.

Permite trocar implementação (Playwright, Evolution, Cloud API) sem mudar código do domínio.
"""
from typing import Protocol, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WhatsAppMessage:
    """Mensagem do WhatsApp (formato padronizado)."""
    id: str                          # ID único da mensagem
    group_id: str                    # ID/nome do grupo
    sender: str                      # Número do remetente
    text: str                        # Texto da mensagem
    timestamp: int                   # Unix timestamp
    has_media: bool = False          # Tem mídia anexada?
    media_url: Optional[str] = None  # URL da mídia (se houver)


@dataclass
class ConnectionStatus:
    """Status de uma conexão WhatsApp."""
    status: str                      # disconnected, qr_needed, connected, error
    is_authenticated: bool
    last_seen: Optional[datetime] = None
    error: Optional[str] = None
    qr_code: Optional[str] = None    # QR Code base64 (se qr_needed)


class WhatsAppGateway(Protocol):
    """
    Interface abstrata para WhatsApp providers.
    
    Qualquer implementação (Playwright, Evolution, Cloud API) deve seguir este contrato.
    Isso permite trocar provider sem modificar lógica de negócio.
    """
    
    async def send_message(
        self,
        connection_id: str,
        group_name: str,
        text: str,
        wait_for_preview: bool = True
    ) -> dict:
        """
        Envia mensagem para grupo.
        
        Args:
            connection_id: ID da conexão WhatsApp
            group_name: Nome do grupo (busca por nome)
            text: Texto da mensagem
            wait_for_preview: Aguardar geração de preview?
            
        Returns:
            {
                "status": "sent" | "error",
                "preview_generated": bool,
                "duration_ms": int,
                "error": str (opcional)
            }
        """
        ...
    
    async def get_new_messages(
        self,
        connection_id: str,
        source_groups: List[str]
    ) -> List[WhatsAppMessage]:
        """
        Obtém novas mensagens dos grupos fonte.
        
        Args:
            connection_id: ID da conexão
            source_groups: Lista de nomes de grupos para monitorar
            
        Returns:
            Lista de mensagens novas (já filtradas por deduplicação)
        """
        ...
    
    async def get_connection_status(
        self,
        connection_id: str
    ) -> ConnectionStatus:
        """
        Verifica status da conexão.
        
        Returns:
            ConnectionStatus com informações atuais
        """
        ...
    
    async def disconnect(
        self,
        connection_id: str
    ) -> None:
        """
        Desconecta número WhatsApp.
        """
        ...
    
    async def get_qr_code(
        self,
        connection_id: str
    ) -> Optional[str]:
        """
        Obtém QR Code para autenticação (se necessário).
        
        Returns:
            QR Code em base64 ou None se já conectado
        """
        ...
