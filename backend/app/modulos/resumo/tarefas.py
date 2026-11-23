"""RF24: envio do resumo pelo worker do Celery (agenda em app/nucleo/tarefas.py)."""

import logging
from datetime import date, datetime

from sqlalchemy import select

from app.integracoes.wpp import obter_whatsapp

# O worker não carrega a API: registra a tblConta e a tblCategoria, lidas no resumo
from app.modulos.contas import modelos as _modelos_contas  # noqa: F401
from app.modulos.identidade.modelos import Usuario
from app.modulos.resumo.servico import Periodo, montar_resumo, texto_resumo
from app.modulos.transacoes.servico import FUSO_BRASILIA
from app.nucleo.banco import SessaoLocal
from app.nucleo.tarefas import fila

logger = logging.getLogger(__name__)


def enviar_resumos(periodo: Periodo, hoje: date | None = None) -> int:
    """Manda o resumo a quem tem WhatsApp e resumo ligados e um número cadastrado.
    Falha com uma pessoa não interrompe as demais. Devolve quantos foram enviados."""
    hoje = hoje or datetime.now(FUSO_BRASILIA).date()
    wpp = obter_whatsapp()
    enviados = 0

    with SessaoLocal() as sessao:
        usuarios = sessao.scalars(
            select(Usuario).where(
                Usuario.resumo_ativo.is_(True),
                Usuario.whatsapp_ativo.is_(True),
                Usuario.telefone.is_not(None),
            )
        ).all()
        for usuario in usuarios:
            try:
                resumo = montar_resumo(sessao, usuario.id, periodo, hoje)
                if resumo is None:
                    continue
                wpp.enviar(
                    destinatario=f"{usuario.telefone}@s.whatsapp.net",
                    assunto=f"Resumo {periodo.value}",
                    texto=texto_resumo(resumo),
                )
                enviados += 1
            except Exception:
                logger.exception("Falha ao enviar o resumo do usuário %s", usuario.id)

    # Só a quantidade: sem telefone nem valores no log (RNF05)
    logger.info("Resumos %s enviados: %d", periodo.value, enviados)
    return enviados


@fila.task(name="resumo.semanal")
def resumo_semanal() -> int:
    """Toda segunda-feira, sobre os 7 dias anteriores."""
    return enviar_resumos(Periodo.SEMANAL)


@fila.task(name="resumo.mensal")
def resumo_mensal() -> int:
    """Todo dia 1º, sobre o mês anterior."""
    return enviar_resumos(Periodo.MENSAL)
