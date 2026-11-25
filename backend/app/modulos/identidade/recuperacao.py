"""Troca do PIN e "esqueci meu PIN".

O código de 6 dígitos vai por e-mail e fica no Valkey só como hash, com validade.
Ao trocar ou redefinir o PIN, a versão do token sobe e as sessões antigas caem.

O pedido de código responde igual com ou sem conta (RNF05): os limites de pedidos
contam por celular, e só quem tem conta recebe um código.
"""

import hashlib
import hmac
import logging
import secrets
from datetime import timedelta
from enum import Enum

import valkey
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modulos.identidade import servico
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import gerar_hash, hash_telefone
from app.nucleo.config import settings
from app.nucleo.portas import FalhaEnvioEmail, PortaEmail

logger = logging.getLogger(__name__)

cliente = valkey.Valkey.from_url(settings.VALKEY_URL, decode_responses=True)


class Limites(Enum):
    """Política do código de recuperação."""

    VALIDADE_CODIGO = timedelta(minutes=15)
    TENTATIVAS_CODIGO = 5
    ESPERA_REENVIO = timedelta(seconds=60)
    PEDIDOS_POR_HORA = 5


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


def pedir_codigo(sessao: Session, telefone: str) -> tuple[Usuario, str] | None:
    """Gera um código novo (o anterior deixa de valer). Quem chama envia o e-mail.

    Devolve None quando o celular não tem conta; quem chama responde igual nos dois casos.
    """
    hash_tel = hash_telefone(telefone)
    chave_espera = _chave("espera", hash_tel)
    chave_pedidos = _chave("pedidos", hash_tel)
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

        usuario = sessao.scalar(
            select(Usuario).where(Usuario.hash_telefone == hash_tel)
        )
        if usuario is None:
            return None

        codigo = f"{secrets.randbelow(10**6):06d}"
        chave_codigo = _chave("codigo", usuario.id)
        pipe = cliente.pipeline()
        pipe.delete(chave_codigo)
        pipe.hset(chave_codigo, mapping={"hash": _hash(codigo), "tentativas": 0})
        pipe.expire(chave_codigo, Limites.VALIDADE_CODIGO.value)
        pipe.execute()
    except valkey.ValkeyError:
        raise RecuperacaoIndisponivel from None
    return usuario, codigo


def enviar_codigo(
    email: PortaEmail, usuario: Usuario, telefone: str, assunto: str, texto: str
) -> None:
    """Roda em segundo plano, depois da resposta. Se o envio falhar, o código é
    descartado e a espera é liberada, para a pessoa poder pedir outro na hora."""
    try:
        email.enviar(usuario.email, assunto, texto)
    except FalhaEnvioEmail:
        hash_tel = hash_telefone(telefone)
        try:
            pipe = cliente.pipeline()
            pipe.delete(_chave("codigo", usuario.id))
            pipe.delete(_chave("espera", hash_tel))
            pipe.decr(_chave("pedidos", hash_tel))
            pipe.execute()
        except valkey.ValkeyError:
            logger.warning("Não foi possível liberar um novo pedido de código.")


def redefinir_pin(
    sessao: Session, telefone: str, codigo: str, novo_pin: str
) -> Usuario:
    """Confere o código e grava o novo PIN. Também desbloqueia a conta (D17)."""
    usuario = sessao.scalar(
        select(Usuario)
        .where(Usuario.hash_telefone == hash_telefone(telefone))
        .with_for_update()
    )
    if usuario is None:
        raise CodigoErrado

    chave = _chave("codigo", usuario.id)
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
    sessao.refresh(usuario, with_for_update=True)
    servico.conferir_pin(sessao, usuario, pin_atual)
    _gravar_novo_pin(sessao, usuario, novo_pin)
    return usuario


def _gravar_novo_pin(sessao: Session, usuario: Usuario, novo_pin: str) -> None:
    usuario.hash_pin = gerar_hash(novo_pin)
    usuario.tentativas = 0
    usuario.bloqueado_ate = None
    usuario.versao_token += 1
    sessao.commit()


def _chave(tipo: str, identificador: object) -> str:
    """O código fica pelo id do usuário; espera e pedidos, pelo hash do celular."""
    return f"vero:recuperacao:{tipo}:{identificador}"


def _hash(codigo: str) -> str:
    # Chave própria, separada da SECRET_KEY que assina o token
    return hmac.new(
        settings.CHAVE_CODIGO_RECUPERACAO.encode(), codigo.encode(), hashlib.sha256
    ).hexdigest()
