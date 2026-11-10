"""Troca do PIN e "esqueci meu PIN".

O código de 6 dígitos vai por e-mail e fica no Valkey só como hash, com validade.
Ao trocar ou redefinir o PIN, a versão do token sobe e as sessões antigas caem.
"""

import hashlib
import hmac
import secrets
from datetime import timedelta
from enum import Enum

import valkey
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modulos.identidade import servico
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import gerar_hash
from app.nucleo.config import settings

cliente = valkey.Valkey.from_url(settings.VALKEY_URL, decode_responses=True)


class Limites(Enum):
    """Política do código de recuperação."""

    VALIDADE_CODIGO = timedelta(minutes=15)
    TENTATIVAS_CODIGO = 5
    ESPERA_REENVIO = timedelta(seconds=60)
    PEDIDOS_POR_HORA = 5


class CelularSemConta(Exception):
    pass


class EspereNovoCodigo(Exception):
    def __init__(self, segundos_restantes: int) -> None:
        super().__init__(segundos_restantes)
        self.segundos_restantes = segundos_restantes


class MuitosCodigos(Exception):
    pass


class CodigoErrado(Exception):
    pass


class RecuperacaoIndisponivel(Exception):
    """O Valkey não respondeu."""


def mascarar_email(email: str) -> str:
    """joao@gmail.com -> j***@gmail.com"""
    usuario, dominio = email.split("@", 1)
    return f"{usuario[0]}***@{dominio}"


def pedir_codigo(sessao: Session, telefone: str) -> tuple[Usuario, str]:
    """Gera um código novo (o anterior deixa de valer). Quem chama envia o e-mail."""
    usuario = sessao.scalar(select(Usuario).where(Usuario.telefone == telefone))
    if usuario is None:
        raise CelularSemConta

    chave_espera = _chave("espera", usuario)
    chave_pedidos = _chave("pedidos", usuario)
    chave_codigo = _chave("codigo", usuario)
    codigo = f"{secrets.randbelow(10**6):06d}"
    try:
        espera = int(Limites.ESPERA_REENVIO.value.total_seconds())
        if not cliente.set(chave_espera, 1, nx=True, ex=espera):
            raise EspereNovoCodigo(max(1, cliente.ttl(chave_espera)))

        pipe = cliente.pipeline()
        pipe.incr(chave_pedidos)
        pipe.expire(chave_pedidos, timedelta(hours=1), nx=True)
        pedidos, _ = pipe.execute()
        if pedidos > Limites.PEDIDOS_POR_HORA.value:
            raise MuitosCodigos

        pipe = cliente.pipeline()
        pipe.delete(chave_codigo)
        pipe.hset(chave_codigo, mapping={"hash": _hash(codigo), "tentativas": 0})
        pipe.expire(chave_codigo, Limites.VALIDADE_CODIGO.value)
        pipe.execute()
    except valkey.ValkeyError:
        raise RecuperacaoIndisponivel from None
    return usuario, codigo


def redefinir_pin(
    sessao: Session, telefone: str, codigo: str, novo_pin: str
) -> Usuario:
    """Confere o código e grava o novo PIN. Também desbloqueia a conta (D17)."""
    usuario = sessao.scalar(
        select(Usuario).where(Usuario.telefone == telefone).with_for_update()
    )
    if usuario is None:
        raise CodigoErrado

    chave = _chave("codigo", usuario)
    try:
        pipe = cliente.pipeline()
        pipe.hget(chave, "hash")
        pipe.hincrby(chave, "tentativas", 1)
        hash_salvo, tentativas = pipe.execute()

        if hash_salvo is None:
            # Código vencido: apaga o que o hincrby criou sem validade
            cliente.delete(chave)
            raise CodigoErrado
        if not hmac.compare_digest(hash_salvo, _hash(codigo)):
            if tentativas >= Limites.TENTATIVAS_CODIGO.value:
                cliente.delete(chave)
            raise CodigoErrado
        if tentativas > Limites.TENTATIVAS_CODIGO.value:
            cliente.delete(chave)
            raise CodigoErrado
        # Só um pedido usa o código: quem apagar primeiro leva
        if not cliente.delete(chave):
            raise CodigoErrado
    except valkey.ValkeyError:
        raise RecuperacaoIndisponivel from None

    _gravar_novo_pin(sessao, usuario, novo_pin)
    return usuario


def trocar_pin(
    sessao: Session, usuario: Usuario, pin_atual: str, novo_pin: str
) -> Usuario:
    """Troca com login. PIN atual errado conta como tentativa (D17).

    Pode lançar servico.CredenciaisInvalidas ou servico.ContaBloqueada."""
    usuario = servico.autenticar(sessao, usuario.telefone, pin_atual)
    _gravar_novo_pin(sessao, usuario, novo_pin)
    return usuario


def _gravar_novo_pin(sessao: Session, usuario: Usuario, novo_pin: str) -> None:
    usuario.hash_pin = gerar_hash(novo_pin)
    usuario.tentativas = 0
    usuario.bloqueado_ate = None
    usuario.versao_token += 1
    sessao.commit()


def _chave(tipo: str, usuario: Usuario) -> str:
    return f"vero:recuperacao:{tipo}:{usuario.id}"


def _hash(codigo: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(), codigo.encode(), hashlib.sha256
    ).hexdigest()
