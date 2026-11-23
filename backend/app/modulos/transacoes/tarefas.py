"""Tarefas do módulo de transações executadas pelo worker do Celery."""

import logging
from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm.session import Session

from app.integracoes.wpp import obter_whatsapp
from app.modulos.assistente.mensagens import formatar_moeda
from app.modulos.contas.modelos import Conta

# O worker não carrega a API: registra a tblUsuario, alvo da FK da tblConta
from app.modulos.identidade import modelos as _modelos_identidade
from app.modulos.transacoes import servico
from app.nucleo.banco import SessaoLocal
from app.nucleo.portas import PortaWhatsApp
from app.nucleo.tarefas import fila

logger = logging.getLogger(__name__)


def _buscar_contas_vencendo_hoje(
    sessao: Session, data_referencia: date
) -> Sequence[Conta]:
    """Contas que vencem na data de referência e ainda não foram pagas."""
    stmt = select(Conta).where(
        Conta.vencimento_em == data_referencia, Conta.pagamento_em.is_(None)
    )
    return sessao.scalars(stmt).all()


def _montar_texto_lembrete(conta: Conta) -> str:
    descricao = conta.descricao or "sem descrição"
    valor = formatar_moeda(round(conta.valor * 100))
    return (
        f"Lembrete: sua conta '{descricao}' vence hoje, no valor de {valor}. "
        "Pague hoje para evitar juros."
    )


def _enviar_notificacao(
    wpp: PortaWhatsApp, usuario: _modelos_identidade.Usuario, texto: str
) -> None:
    wpp.enviar(
        destinatario=f"{usuario.telefone}@s.whatsapp.net",
        assunto="Lembrete de vencimento",
        texto=texto,
    )


@fila.task(name="transacoes.lancar_gastos_fixos")
def lancar_gastos_fixos() -> int:
    """RF18 e RF37: disparada todo dia pelo Celery Beat (ver app/nucleo/tarefas.py)."""
    with SessaoLocal() as sessao:
        lancadas = servico.lancar_gastos_fixos(sessao)
    # Só a quantidade: sem usuário nem valores no log (RNF05)
    logger.info("Gastos fixos lançados: %d", lancadas)
    return lancadas


@fila.task(name="transacoes.lembretes_whatsapp")
def lembretes_whatsapp() -> int:
    """RF28: lembrete no WhatsApp no dia do vencimento (Celery Beat, 9h de Brasília).

    Só avisa: o gasto entra no saldo quando a pessoa marca a conta como paga (RF30).
    Pula quem desligou o WhatsApp e quem não tem número, sem interromper os demais.
    """
    hoje = datetime.now(servico.FUSO_BRASILIA).date()
    wpp = obter_whatsapp()
    enviadas = 0
    sem_telefone = 0

    with SessaoLocal() as sessao:
        for conta in _buscar_contas_vencendo_hoje(sessao, hoje):
            usuario = sessao.get(_modelos_identidade.Usuario, conta.usuario_id)
            if usuario is None or not usuario.whatsapp_ativo:
                continue
            if not usuario.telefone:
                sem_telefone += 1
                continue
            try:
                _enviar_notificacao(wpp, usuario, _montar_texto_lembrete(conta))
                enviadas += 1
            except Exception:
                logger.exception("Falha ao enviar lembrete da conta %s", conta.id)

    # Só quantidades: sem telefone nem valores no log (RNF05)
    logger.info(
        "Lembretes WhatsApp enviados: %d (sem telefone: %d)", enviadas, sem_telefone
    )
    return enviadas
