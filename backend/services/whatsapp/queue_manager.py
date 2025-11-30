"""
Queue Manager - Gerencia filas de envio com rate limit duplo.

Rate limit em dois níveis:
1. Por grupo destino (6-10 min entre mensagens)
2. Global por conexão (máx 1 msg a cada 30s, independente do grupo)
"""
import time
import logging
from typing import Dict, Deque, Optional
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QueuedMessage:
    """Mensagem na fila para ser enviada."""
    connection_id: str
    group_name: str
    text: str
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class QueueManager:
    """
    Gerencia filas de envio com rate limit em dois níveis.
    
    Garante:
    - Intervalo mínimo entre mensagens no MESMO grupo
    - Intervalo mínimo global para a CONEXÃO (evita burst)
    """
    
    def __init__(self):
        # Filas por grupo
        self.queues: Dict[str, Deque[QueuedMessage]] = {}
        
        # Último envio por grupo
        self.last_sent_per_group: Dict[str, float] = {}
        
        # Último envio por conexão (GLOBAL)
        self.last_sent_per_connection: Dict[str, float] = {}
        
        logger.info("QueueManager initialized")
    
    def add(
        self,
        connection_id: str,
        group_name: str,
        text: str
    ) -> None:
        """
        Adiciona mensagem à fila do grupo.
        
        Args:
            connection_id: ID da conexão WhatsApp
            group_name: Nome do grupo destino
            text: Texto da mensagem
        """
        msg = QueuedMessage(
            connection_id=connection_id,
            group_name=group_name,
            text=text
        )
        
        # Criar fila se não existir
        if group_name not in self.queues:
            self.queues[group_name] = deque()
        
        self.queues[group_name].append(msg)
        logger.debug(f"Message queued for {group_name} (queue size: {len(self.queues[group_name])})")
    
    def can_send(
        self,
        connection_id: str,
        group_name: str,
        min_interval_per_group: int = 360,     # 6 minutos
        min_interval_global: int = 30          # 30 segundos
    ) -> bool:
        """
        Verifica se pode enviar mensagem (rate limit duplo).
        
        Args:
            connection_id: ID da conexão
            group_name: Nome do grupo
            min_interval_per_group: Intervalo mínimo por grupo (segundos)
            min_interval_global: Intervalo mínimo global (segundos)
            
        Returns:
            True se pode enviar agora
        """
        now = time.time()
        
        # 1. Verificar intervalo POR GRUPO
        last_group = self.last_sent_per_group.get(group_name, 0)
        time_since_last_group = now - last_group
        
        if time_since_last_group < min_interval_per_group:
            seconds_remaining = int(min_interval_per_group - time_since_last_group)
            logger.debug(
                f"Rate limit (group): {group_name} needs {seconds_remaining}s more"
            )
            return False
        
        # 2. Verificar intervalo GLOBAL da conexão
        last_conn = self.last_sent_per_connection.get(connection_id, 0)
        time_since_last_conn = now - last_conn
        
        if time_since_last_conn < min_interval_global:
            seconds_remaining = int(min_interval_global - time_since_last_conn)
            logger.debug(
                f"Rate limit (global): connection {connection_id} needs {seconds_remaining}s more"
            )
            return False
        
        return True
    
    def mark_sent(
        self,
        connection_id: str,
        group_name: str
    ) -> None:
        """
        Marca que mensagem foi enviada (atualiza ambos os contadores).
        
        Args:
            connection_id: ID da conexão
            group_name: Nome do grupo
        """
        now = time.time()
        self.last_sent_per_group[group_name] = now
        self.last_sent_per_connection[connection_id] = now
        
        logger.debug(f"Sent marked for {group_name} (connection {connection_id})")
    
    def get_next(
        self,
        group_name: str
    ) -> Optional[QueuedMessage]:
        """
        Obtém próxima mensagem da fila do grupo (sem remover).
        
        Args:
            group_name: Nome do grupo
            
        Returns:
            Próxima mensagem ou None se fila vazia
        """
        queue = self.queues.get(group_name)
        if queue and len(queue) > 0:
            return queue[0]
        return None
    
    def pop(
        self,
        group_name: str
    ) -> Optional[QueuedMessage]:
        """
        Remove e retorna próxima mensagem da fila.
        
        Args:
            group_name: Nome do grupo
            
        Returns:
            Mensagem removida ou None
        """
        queue = self.queues.get(group_name)
        if queue and len(queue) > 0:
            return queue.popleft()
        return None
    
    def get_queue_size(self, group_name: str) -> int:
        """Retorna tamanho da fila de um grupo."""
        queue = self.queues.get(group_name)
        return len(queue) if queue else 0
    
    def get_total_queued(self) -> int:
        """Retorna total de mensagens em todas as filas."""
        return sum(len(q) for q in self.queues.values())
    
    def get_time_until_next_send(
        self,
        connection_id: str,
        group_name: str,
        min_interval_per_group: int = 360,
        min_interval_global: int = 30
    ) -> int:
        """
        Retorna tempo em segundos até poder enviar próxima mensagem.
        
        Returns:
            Segundos até liberar (0 se já pode enviar)
        """
        now = time.time()
        
        # Verificar por grupo
        last_group = self.last_sent_per_group.get(group_name, 0)
        wait_group = max(0, min_interval_per_group - (now - last_group))
        
        # Verificar global
        last_conn = self.last_sent_per_connection.get(connection_id, 0)
        wait_global = max(0, min_interval_global - (now - last_conn))
        
        # Retornar o maior dos dois
        return int(max(wait_group, wait_global))
    
    def clear_old_queues(self, max_age_hours: int = 24):
        """
        Remove filas antigas (mensagens que estão há muito tempo esperando).
        
        Args:
            max_age_hours: Idade máxima em horas
        """
        now = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for group_name, queue in list(self.queues.items()):
            if queue:
                # Remover mensagens muito antigas
                while queue and (now - queue[0].created_at) > max_age_seconds:
                    old_msg = queue.popleft()
                    logger.warning(f"Removed old message from {group_name} queue (age: {(now - old_msg.created_at) / 3600:.1f}h)")
                
                # Remover fila se vazia
                if len(queue) == 0:
                    del self.queues[group_name]
