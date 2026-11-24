"""Tarefas do módulo de transações executadas pelo worker do Celery."""

import logging
import uuid
from datetime import date, datetime, timedelta
from enum import Enum

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm.session import Session

from app.integracoes.wpp import obter_whatsapp
from app.modulos.assistente.mensagens import formatar_moeda
from app.modulos.contas import servico as servico_contas
from app.modulos.contas.esquemas import ContaAVencer

# O worker não carrega a API: registra a tblUsuario, alvo da FK da tblConta
from app.modulos.identidade import modelos as _modelos_identidade
from app.modulos.transacoes import servico
from app.modulos.transacoes.esquemas import CanalAviso, MomentoAviso
from app.modulos.transacoes.mensagens import Message
from app.modulos.transacoes.modelos import Aviso
from app.nucleo.banco import SessaoLocal
from app.nucleo.portas import PortaWhatsApp
from app.nucleo.tarefas import fila

logger = logging.getLogger(__name__)


class Lembrete(Enum):
    """Limites do lembrete de vencimento."""

    # Maior antecedência aceita no nuDiasAlerta da pessoa
    DIAS_ALERTA_MAXIMO = 30


def _montar_texto_lembrete(conta: ContaAVencer) -> str:
    """RF28: aviso no dia do vencimento."""
    return Message.LEMBRETE_NO_DIA.message.format(
        descricao=conta.descricao or Message.LEMBRETE_SEM_DESCRICAO.message,
        valor=formatar_moeda(round(conta.valor * 100)),
    )


def _montar_texto_antecipado(conta: ContaAVencer, faltam: int) -> str:
    """RF29: aviso dias antes, para dar tempo de separar o dinheiro."""
    quando = (
        Message.LEMBRETE_AMANHA.message
        if faltam == 1
        else Message.LEMBRETE_EM_DIAS.message.format(dias=faltam)
    )
    return Message.LEMBRETE_ANTECIPADO.message.format(
        descricao=conta.descricao or Message.LEMBRETE_SEM_DESCRICAO.message,
        quando=quando,
        data=conta.vencimento_em.strftime("%d/%m"),
        valor=formatar_moeda(round(conta.valor * 100)),
    )


def _momento_do_aviso(
    conta: ContaAVencer, hoje: date, dias_alerta: int
) -> MomentoAviso | None:
    """No dia do vencimento, o aviso do dia (RF28). Faltando de 1 até `dias_alerta`
    dias, o antecipado (RF29); assim a conta cadastrada já em cima do prazo, ou um dia
    em que a rotina não rodou, ainda recebem o aviso antecipado uma vez."""
    faltam = (conta.vencimento_em - hoje).days
    if faltam == 0:
        return MomentoAviso.NO_DIA
    if 1 <= faltam <= dias_alerta:
        return MomentoAviso.ANTECIPADO
    return None


def _registrar_aviso(
    sessao: Session, conta_id: uuid.UUID, momento: MomentoAviso, texto: str
) -> bool:
    """Grava o aviso antes de enviar. Devolve False se ele já tinha sido enviado; o
    banco aceita um só por conta, momento e canal, mesmo com duas rotinas ao mesmo
    tempo."""
    comando = (
        insert(Aviso)
        .values(
            conta_id=conta_id,
            momento=momento,
            canal=CanalAviso.WHATSAPP,
            mensagem=texto,
        )
        .on_conflict_do_nothing(
            index_elements=[Aviso.conta_id, Aviso.momento, Aviso.canal]
        )
        .returning(Aviso.id)
    )
    return sessao.scalar(comando) is not None


def _enviar_notificacao(
    wpp: PortaWhatsApp, usuario: _modelos_identidade.Usuario, texto: str
) -> None:
    wpp.enviar(
        destinatario=f"{usuario.telefone}@s.whatsapp.net",
        assunto=Message.LEMBRETE_ASSUNTO.message,
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
    """RF28 e RF29: lembretes no WhatsApp (Celery Beat, 9h de Brasília). Avisa no dia
    do vencimento e, antes, com a antecedência que a pessoa escolheu (nuDiasAlerta).

    Só avisa: o gasto entra no saldo quando a pessoa marca a conta como paga (RF30).
    Conta paga não é avisada, e cada aviso sai uma vez só (tblAviso), mesmo que a
    rotina rode de novo. Pula quem desligou o WhatsApp e quem não tem número, sem
    interromper os demais; se o envio falhar, o aviso não fica registrado e sai na
    próxima vez.
    """
    hoje = datetime.now(servico.FUSO_BRASILIA).date()
    ate = hoje + timedelta(days=Lembrete.DIAS_ALERTA_MAXIMO.value)
    wpp = obter_whatsapp()
    enviadas = 0
    sem_telefone = 0

    with SessaoLocal() as sessao:
        for conta in servico_contas.contas_em_aberto_entre(sessao, hoje, ate):
            usuario = sessao.get(_modelos_identidade.Usuario, conta.usuario_id)
            if usuario is None or not usuario.whatsapp_ativo:
                continue
            momento = _momento_do_aviso(conta, hoje, usuario.dias_alerta or 0)
            if momento is None:
                continue
            if not usuario.telefone:
                sem_telefone += 1
                continue

            texto = (
                _montar_texto_lembrete(conta)
                if momento == MomentoAviso.NO_DIA
                else _montar_texto_antecipado(conta, (conta.vencimento_em - hoje).days)
            )
            ponto = sessao.begin_nested()
            if not _registrar_aviso(sessao, conta.id, momento, texto):
                ponto.rollback()
                continue
            try:
                _enviar_notificacao(wpp, usuario, texto)
            except Exception:
                ponto.rollback()
                logger.exception("Falha ao enviar lembrete da conta %s", conta.id)
                continue
            ponto.commit()
            sessao.commit()
            enviadas += 1

    # Só quantidades: sem telefone nem valores no log (RNF05)
    logger.info(
        "Lembretes WhatsApp enviados: %d (sem telefone: %d)", enviadas, sem_telefone
    )
    return enviadas
