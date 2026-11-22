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


fila = Celery(
    "vero",
    broker=settings.VALKEY_URL,
    include=["app.modulos.transacoes.tarefas"],
)
fila.conf.timezone = "America/Sao_Paulo"
fila.conf.beat_schedule = {
    "lancar-gastos-fixos": {
        "task": "transacoes.lancar_gastos_fixos",
        "schedule": Agenda.GASTOS_FIXOS.value,
    },
}
