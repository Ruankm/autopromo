"""
Segurança: hashing de senha, geração e validação de JWT.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt  # Usando bcrypt direto ao invés de passlib para evitar bugs no Python 3.14
from .config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha plain bate com o hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """
    Gera hash bcrypt da senha.
    
    Bcrypt tem um limite de 72 bytes. Senhas maiores são truncadas
    automaticamente para evitar ValueError.
    """
    # Truncar para 72 bytes (limite do bcrypt)
    password_bytes = password.encode('utf-8')[:72]
    
    # Gerar hash (bcrypt retorna bytes)
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    
    # Retornar como string UTF-8
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um JWT access token.
    
    Args:
        data: Dict com claims (ex: {"sub": user_id})
        expires_delta: Tempo de expiração customizado
    
    Returns:
        Token JWT encodificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica e valida um JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Payload do token ou None se inválido
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
