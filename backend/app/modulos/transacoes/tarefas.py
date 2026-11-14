"""Tarefas do módulo de transações executadas pelo worker do Celery."""

import logging

# O worker não carrega a API: registra a tblUsuario, alvo da FK da tblConta
from app.modulos.identidade import modelos as _modelos_identidade  # noqa: F401
from app.modulos.transacoes import servico
from app.nucleo.banco import SessaoLocal
from app.nucleo.tarefas import fila

logger = logging.getLogger(__name__)


@fila.task(name="transacoes.lancar_gastos_fixos")
def lancar_gastos_fixos() -> int:
    """RF18: disparada todo dia pelo Celery Beat (ver app/nucleo/tarefas.py)."""
    with SessaoLocal() as sessao:
        lancadas = servico.lancar_gastos_fixos(sessao)
    # Só a quantidade: sem usuário nem valores no log (RNF05)
    logger.info("Gastos fixos lançados: %d", lancadas)
    return lancadas
