"""
WhatsApp Evolution API Client.

Cliente para integração com Evolution API (WhatsApp Gateway).
Gerencia criação de instâncias, QR Codes, status e envio de mensagens.
"""
import httpx
from typing import Optional, List, Dict


class EvolutionAPIClient:
    """Cliente para Evolution API."""
    
    def __init__(self, api_url: str, api_key: str):
        """
        Inicializa cliente.
        
        Args:
            api_url: URL base da Evolution API (ex: http://localhost:8081)
            api_key: API Key global da Evolution
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "apikey": api_key,
            "Content-Type": "application/json"
        }
    
    async def create_instance(self, instance_name: str) -> Dict:
        """
        Cria nova instância WhatsApp.
        
        Args:
            instance_name: Nome único da instância
            
        Returns:
            Dict com dados da instância criada (inclui QR Code se disponível)
        """
        url = f"{self.api_url}/instance/create"
        payload = {
            "instanceName": instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_connection_status(self, instance_name: str) -> Dict:
        """
        Verifica status da conexão.
        
        Args:
            instance_name: Nome da instância
            
        Returns:
            Dict com 'state': 'open' | 'close' | 'connecting'
        """
        url = f"{self.api_url}/instance/connectionState/{instance_name}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def fetch_all_groups(self, instance_name: str) -> List[Dict]:
        """
        Lista todos os grupos do WhatsApp.
        
        Args:
            instance_name: Nome da instância
            
        Returns:
            Lista de grupos: [{"id": "...", "subject": "...", "size": 123}, ...]
        """
        url = f"{self.api_url}/group/fetchAllGroups/{instance_name}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def send_message(self, instance_name: str, chat_id: str, text: str) -> Dict:
        """
        Envia mensagem de texto.
        
        Args:
            instance_name: Nome da instância
            chat_id: ID do chat/grupo (ex: 120363...@g.us)
            text: Texto da mensagem
            
        Returns:
            Dict com resposta da API
        """
        url = f"{self.api_url}/message/sendText/{instance_name}"
        payload = {
            "number": chat_id,
            "text": text
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def delete_instance(self, instance_name: str) -> Dict:
        """
        Deleta instância.
        
        Args:
            instance_name: Nome da instância
            
        Returns:
            Dict com resposta
        """
        url = f"{self.api_url}/instance/delete/{instance_name}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(url, headers=self.headers)
            response.raise_for_status()
            return response.json()


# Alias para compatibilidade
WhatsAppEvolutionClient = EvolutionAPIClient
