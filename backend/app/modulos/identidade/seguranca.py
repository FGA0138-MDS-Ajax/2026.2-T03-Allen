"""Hash de senha e PIN (bcrypt) e tokens de sessão (JWT)."""

import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.modulos.identidade.mensagens import Message
from app.modulos.identidade.modelos import Usuario
from app.nucleo.banco import obter_sessao
from app.nucleo.config import settings

esquema_bearer = HTTPBearer(auto_error=False)


def gerar_hash(valor: str) -> str:
    return bcrypt.hashpw(valor.encode(), bcrypt.gensalt()).decode()


def conferir_hash(valor: str, hash_salvo: str) -> bool:
    return bcrypt.checkpw(valor.encode(), hash_salvo.encode())


# Hash determinístico para telefone (HMAC-SHA256 com SECRET_KEY como pepper)
# O mesmo telefone sempre gera o mesmo hash, permitindo buscas e unique constraint.
def hash_telefone(valor: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), valor.encode(), hashlib.sha256).hexdigest()


# Conferido quando o celular não existe, para a resposta levar o mesmo tempo
HASH_FICTICIO = gerar_hash("vero-hash-ficticio")


def criar_token(id_usuario: uuid.UUID, metodo: str, duracao: timedelta) -> str:
    agora = datetime.now(UTC)
    dados = {
        "sub": str(id_usuario),
        "perfil": "titular",
        "metodo": metodo,
        "iat": agora,
        "exp": agora + duracao,
    }
    return jwt.encode(dados, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITMO)


def ler_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITMO],
        options={"require": ["sub", "exp"]},
    )


def usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    sessao: Session = Depends(obter_sessao),
) -> Usuario:
    """Dependência das rotas que exigem login."""
    nao_autorizado = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=Message.SESSAO_INVALIDA,
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credenciais is None:
        raise nao_autorizado
    try:
        id_usuario = uuid.UUID(ler_token(credenciais.credentials)["sub"])
    except (jwt.PyJWTError, ValueError):
        raise nao_autorizado from None

    usuario = sessao.get(Usuario, id_usuario)
    if usuario is None:
        raise nao_autorizado
    return usuario
