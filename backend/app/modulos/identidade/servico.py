"""Regras de cadastro, login e bloqueio por tentativas."""

import math
from datetime import UTC, datetime, timedelta
from enum import Enum

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modulos.identidade.esquemas import CadastroEntrada
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import HASH_FICTICIO, conferir_hash, gerar_hash


class Attempts(Enum):
    """política de tempo e número de tentativas de acesso do usuario"""

    MAX_TENTATIVAS = 5
    TEMPO_BLOQUEIO = timedelta(seconds=30)
    # DURACAO_TOKEN_SENHA = timedelta(days=7)
    DURACAO_TOKEN_PIN = timedelta(hours=2)


class TelefoneJaCadastrado(Exception):
    pass


class EmailJaCadastrado(Exception):
    pass


class CredenciaisInvalidas(Exception):
    pass


class ContaBloqueada(Exception):
    def __init__(self, segundos_restantes: int) -> None:
        super().__init__(segundos_restantes)
        self.segundos_restantes = segundos_restantes


def cadastrar(sessao: Session, dados: CadastroEntrada) -> Usuario:
    if sessao.scalar(select(Usuario.id).where(Usuario.telefone == dados.telefone)):
        raise TelefoneJaCadastrado

    email = dados.email.lower()
    if sessao.scalar(select(Usuario.id).where(Usuario.email == email)):
        raise EmailJaCadastrado

    usuario = Usuario(
        nome=dados.nome,
        telefone=dados.telefone,
        email=email,
        hash_pin=gerar_hash(dados.pin),
    )
    sessao.add(usuario)
    try:
        sessao.commit()
    except IntegrityError:
        sessao.rollback()
        raise TelefoneJaCadastrado from None
    sessao.refresh(usuario)
    return usuario


def autenticar(sessao: Session, telefone: str, segredo: str) -> Usuario:
    """Confere o PIN. Após MAX_TENTATIVAS erros seguidos, bloqueia por TEMPO_BLOQUEIO."""
    usuario = sessao.scalar(
        select(Usuario).where(Usuario.telefone == telefone).with_for_update()
    )
    if usuario is None:
        conferir_hash(segredo, HASH_FICTICIO)
        raise CredenciaisInvalidas

    agora = datetime.now(UTC)
    if usuario.bloqueado_ate and usuario.bloqueado_ate > agora:
        sessao.rollback()
        raise ContaBloqueada(_segundos_ate(usuario.bloqueado_ate, agora))

    # if usuario.hash_pin is None:
    #     sessao.rollback()  -> pin agora é obrigatorio
    #     raise PinNaoCriado

    if not conferir_hash(segredo, usuario.hash_pin):
        usuario.tentativas += 1
        bloqueou = usuario.tentativas >= Attempts.MAX_TENTATIVAS.value
        if bloqueou:
            usuario.tentativas = 0
            usuario.bloqueado_ate = agora + Attempts.TEMPO_BLOQUEIO.value
        sessao.commit()
        if bloqueou:
            raise ContaBloqueada(int(Attempts.TEMPO_BLOQUEIO.value.total_seconds()))
        raise CredenciaisInvalidas

    usuario.tentativas = 0
    usuario.bloqueado_ate = None
    sessao.commit()
    return usuario


def _segundos_ate(momento: datetime, agora: datetime) -> int:
    return max(1, math.ceil((momento - agora).total_seconds()))
