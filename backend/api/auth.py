"""API endpoints para autenticação (registro e login)."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import verify_password, get_password_hash, create_access_token
from api.deps import get_current_user
from models.user import User
from schemas.user import UserCreate, UserLogin, UserResponse, Token

router = APIRouter(prefix="/users", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Registra um novo usuário no sistema.
    
    - Verifica se email já existe
    - Hasheia a senha com bcrypt
    - Cria novo registro no banco
    """
    # Verificar se email já existe
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Criar novo usuário
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name or "",  # Use provided name or empty string
        config_json={
            "window_start": "08:00",
            "window_end": "22:00",
            "min_delay_seconds": 300,
            "max_messages_per_day": 100
        }
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user



@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """
    Autentica um usuário e retorna JWT token.
    
    - Aceita form data (application/x-www-form-urlencoded)
    - username = email do usuário
    - password = senha do usuário
    - Retorna JWT token + dados do usuário
    """
    # Buscar usuário por email (username no form é o email)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Criar JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return Token(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user),
):
    """Retorna dados do usuário logado."""
    return current_user


@router.patch("/me/config", response_model=UserResponse)
async def update_user_config(
    config_update: dict,  # Recebe JSON direto para flexibilidade
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza configurações do usuário (janela de horário, blacklist, etc).
    """
    # Atualizar apenas campos enviados
    current_config = dict(current_user.config_json or {})
    current_config.update(config_update)
    
    current_user.config_json = current_config
    
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    return current_user
