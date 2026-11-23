"""Tarefas do módulo de transações executadas pelo worker do Celery."""

import logging
from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm.session import Session

# O worker não carrega a API: registra a tblUsuario, alvo da FK da tblConta
from app.integracoes.wpp import obter_whatsapp
from app.modulos.contas.modelos import Conta
from app.modulos.identidade import modelos as _modelos_identidade  # noqa: F401
from app.modulos.transacoes import servico
from app.modulos.transacoes import servico as servico_transacoes
from app.modulos.transacoes.esquemas import OrigemTransacao, TipoTransacao
from app.nucleo.banco import SessaoLocal
from app.nucleo.tarefas import fila

logger = logging.getLogger(__name__)


def _buscar_contas_vencendo_hoje(
    sessao: Session, data_referencia: date
) -> Sequence[Conta]:
    """procura contas com vencimento do dia de hoje e que ainda nao estao pagas"""
    stmt = select(Conta).where(
        Conta.vencimento_em == data_referencia, Conta.pagamento_em.is_(None)
    )
    return sessao.scalars(stmt).all()


def _montar_texto_lembrete(conta: Conta) -> str:
    descricao = conta.descricao or "sem descrição"
    return (
        f"Lembrete: sua conta '{descricao}' "
        f"vence hoje no valor de R$ {conta.valor:.2f}."
        f"Não se preocupe! Pague para evitar juros."
    )


def _enviar_notificacao(wpp, usuario: _modelos_identidade.Usuario, texto: str) -> None:
    """envia mensagem para contas que estao para vencer no dia de hoje e sem pagamento"""
    wpp.enviar(
        # WARNING: resolver essa parte. precisamos do numero telefone.
        destinatario=f"{usuario.telefone}@swhatsapp.net",
        assunto="Lembrete de vencimento",
        texto=texto,
    )


def _registrar_transacao_lembrete(
    sessao: Session, conta: Conta, data_referencia: date
) -> None:

    servico_transacoes.registrar(
        sessao=sessao,
        usuario_id=conta.usuario_id,
        dados=servico_transacoes.TransacaoRegistroEntrada(
            tipo=TipoTransacao.SAIDA,
            valor=conta.valor,
            origem=OrigemTransacao.WHATSAPP_TEXTO,
            data=data_referencia,
            descricao=f"Lembrete WhatsApp - {conta.descricao or 'conta'}",
            categoria_id=conta.categoria_id,
            chave_externa=f"whatsapper_{conta.id}_{data_referencia}",
        ),
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
    """RF28: enviar lembrete no whatsapp no dia do vencimento.

    - roda diariamente, antes de lancar_gastos_fixos();
    - verifica contas com vencimento_em == hoje e pagamento_em is None;
    - envia alerta por whatsapp e registra a transacao com origem = WHATSAPP_TEXTO.
    """
    hoje = date.today()
    wpp = obter_whatsapp()
    enviadas = 0

    with SessaoLocal() as sessao:
        contas = _buscar_contas_vencendo_hoje(sessao, hoje)
        for conta in contas:
            # WARNING: campo necessário para mandar ao notificacao ao usuario
            usuario: _modelos_identidade.Usuario = sessao.get(
                _modelos_identidade.Usuario, conta.usuario_id
            )
            if not usuario.telefone:
                raise ValueError(
                    "É necessário cadastrar um número de WhatsApp para continuar."
                )

            try:
                texto = _montar_texto_lembrete(conta)
                _enviar_notificacao(wpp, usuario, texto)
                _registrar_transacao_lembrete(sessao, conta, hoje)
                sessao.commit()
                enviadas += 1
            except Exception:
                sessao.rollback()
                logger.exception("Falha ao processar lembrete da conta %s", conta.id)

    logger.info("Lembretes WhatsApp enviados: %d", enviadas)
    return enviadas
