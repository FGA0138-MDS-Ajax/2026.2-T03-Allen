"""Fila de tarefas e rotinas agendadas (D6): Celery, com o Valkey como broker.

Worker: celery -A app.nucleo.tarefas:fila worker
Agendador: celery -A app.nucleo.tarefas:fila beat
"""

from enum import Enum

from celery import Celery
from celery.schedules import crontab

from app.nucleo.config import settings


class Agenda(Enum):
    """Horários das rotinas diárias, no fuso de Brasília."""

    # Logo depois da meia-noite, para o gasto fixo e a parcela caírem no dia do
    # vencimento (RF18, RF37)
    GASTOS_FIXOS = crontab(hour=0, minute=10)
    LEMBRETE_WPP = crontab(hour=9, minute=0)
    # RF24: segunda-feira (sobre a semana anterior) e dia 1º (sobre o mês anterior),
    # depois do lembrete das 9h para não chegarem juntos
    RESUMO_SEMANAL = crontab(hour=9, minute=30, day_of_week="mon")
    RESUMO_MENSAL = crontab(hour=10, minute=0, day_of_month="1")


fila = Celery(
    "vero",
    broker=settings.VALKEY_URL,
    include=[
        "app.modulos.transacoes.tarefas",
        "app.modulos.assistente.tarefas",
        "app.modulos.resumo.tarefas",
    ],
)
fila.conf.timezone = "America/Sao_Paulo"
fila.conf.beat_schedule = {
    "lancar-gastos-fixos": {
        "task": "transacoes.lancar_gastos_fixos",
        "schedule": Agenda.GASTOS_FIXOS.value,
    },
    "enviar-lembrete-whatsapp": {
        "task": "transacoes.lembretes_whatsapp",
        "schedule": Agenda.LEMBRETE_WPP.value,
    },
    "enviar-resumo-semanal": {
        "task": "resumo.semanal",
        "schedule": Agenda.RESUMO_SEMANAL.value,
    },
    "enviar-resumo-mensal": {
        "task": "resumo.mensal",
        "schedule": Agenda.RESUMO_MENSAL.value,
    },
}
