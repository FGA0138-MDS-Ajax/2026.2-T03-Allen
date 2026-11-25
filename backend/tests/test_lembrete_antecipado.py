"""Testes do lembrete antecipado no WhatsApp (RF29) e do aviso sem duplicar (RF28)."""

import contextlib
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modulos.contas.modelos import Conta
from app.modulos.identidade.modelos import Usuario
from app.modulos.transacoes import servico, tarefas
from app.modulos.transacoes.modelos import Aviso


class WhatsAppDeTeste:
    """Guarda as mensagens em vez de enviar; pode falhar de propósito."""

    def __init__(self) -> None:
        self.mensagens: list[tuple[str, str]] = []
        self.fora_do_ar = False

    def enviar(self, destinatario: str, assunto: str, texto: str) -> None:
        if self.fora_do_ar:
            raise RuntimeError("fora do ar")
        self.mensagens.append((destinatario, texto))

    def para(self, telefone: str) -> list[str]:
        return [t for d, t in self.mensagens if d.startswith(f"{telefone}@")]


@pytest.fixture
def wpp(sessao: Session, monkeypatch: pytest.MonkeyPatch) -> WhatsAppDeTeste:
    falso = WhatsAppDeTeste()
    monkeypatch.setattr(tarefas, "SessaoLocal", lambda: contextlib.nullcontext(sessao))
    monkeypatch.setattr(tarefas, "obter_whatsapp", lambda: falso)
    return falso


@pytest.fixture
def hoje(monkeypatch: pytest.MonkeyPatch) -> date:
    """Dia fixo para os testes não dependerem do relógio."""
    dia = date(2026, 11, 24)

    class Relogio(datetime):
        @classmethod
        def now(cls, tz=None):  # noqa: ANN001, ANN206
            return datetime(2026, 11, 24, 9, 0, tzinfo=tz)

    monkeypatch.setattr(tarefas, "datetime", Relogio)
    return dia


def _telefone() -> str:
    return "5561" + uuid.uuid4().hex[:9].translate(str.maketrans("abcdef", "123456"))


def _usuario(sessao: Session, dias_alerta: int = 3, whatsapp: bool = True) -> Usuario:
    u = Usuario(
        id=uuid.uuid4(),
        nome="Maria",
        hash_telefone=uuid.uuid4().hex,
        email=f"maria{uuid.uuid4().hex[:8]}@vero.com",
        hash_pin="x",
        tentativas=0,
        telefone=_telefone(),
        whatsapp_ativo=whatsapp,
        dias_alerta=dias_alerta,
    )
    sessao.add(u)
    sessao.flush()
    return u


def _conta(
    sessao: Session,
    usuario: Usuario,
    vencimento: date,
    paga: bool = False,
    descricao: str | None = "Conta de Luz",
) -> Conta:
    conta = Conta(
        usuario_id=usuario.id,
        vencimento_em=vencimento,
        valor=Decimal("120.00"),
        descricao=descricao,
        pagamento_em=datetime.now(servico.FUSO_BRASILIA) if paga else None,
    )
    sessao.add(conta)
    sessao.flush()
    return conta


def _avisos(sessao: Session, conta: Conta) -> list[str]:
    return list(sessao.scalars(select(Aviso.momento).where(Aviso.conta_id == conta.id)))


def test_avisa_tres_dias_antes_do_vencimento(
    sessao: Session, wpp: WhatsAppDeTeste, hoje: date
) -> None:
    maria = _usuario(sessao)
    conta = _conta(sessao, maria, hoje + timedelta(days=3))

    tarefas.lembretes_whatsapp()

    assert wpp.para(maria.telefone) == [
        "Lembrete: sua conta 'Conta de Luz' vence em 3 dias, no dia 27/11, "
        "no valor de R$ 120,00. Separe o dinheiro para pagar em dia."
    ]
    assert _avisos(sessao, conta) == ["antecipado"]


def test_nao_avisa_antes_da_antecedencia(
    sessao: Session, wpp: WhatsAppDeTeste, hoje: date
) -> None:
    maria = _usuario(sessao)
    _conta(sessao, maria, hoje + timedelta(days=4))

    tarefas.lembretes_whatsapp()

    assert wpp.para(maria.telefone) == []


def test_usa_os_dias_de_alerta_de_cada_pessoa(
    sessao: Session, wpp: WhatsAppDeTeste, hoje: date
) -> None:
    cinco = _usuario(sessao, dias_alerta=5)
    _conta(sessao, cinco, hoje + timedelta(days=5))

    tarefas.lembretes_whatsapp()

    [texto] = wpp.para(cinco.telefone)
    assert "vence em 5 dias, no dia 29/11" in texto


def test_sem_dias_de_alerta_so_recebe_o_aviso_do_dia(
    sessao: Session, wpp: WhatsAppDeTeste, hoje: date
) -> None:
    maria = _usuario(sessao, dias_alerta=0)
    _conta(sessao, maria, hoje + timedelta(days=1))
    _conta(sessao, maria, hoje)

    tarefas.lembretes_whatsapp()

    [texto] = wpp.para(maria.telefone)
    assert "vence hoje" in texto


def test_conta_paga_nao_recebe_aviso(
    sessao: Session, wpp: WhatsAppDeTeste, hoje: date
) -> None:
    maria = _usuario(sessao)
    paga = _conta(sessao, maria, hoje + timedelta(days=3), paga=True)

    tarefas.lembretes_whatsapp()

    assert wpp.para(maria.telefone) == []
    assert _avisos(sessao, paga) == []


def test_rodar_de_novo_nao_duplica_nenhum_aviso(
    sessao: Session, wpp: WhatsAppDeTeste, hoje: date
) -> None:
    maria = _usuario(sessao)
    _conta(sessao, maria, hoje + timedelta(days=3))
    _conta(sessao, maria, hoje)

    primeira = tarefas.lembretes_whatsapp()
    segunda = tarefas.lembretes_whatsapp()

    assert len(wpp.para(maria.telefone)) == 2
    assert (primeira >= 2, segunda) == (True, 0)


def test_antecipado_sai_uma_vez_e_o_do_dia_sai_no_vencimento(
    sessao: Session, wpp: WhatsAppDeTeste, hoje: date, monkeypatch: pytest.MonkeyPatch
) -> None:
    maria = _usuario(sessao)
    conta = _conta(sessao, maria, hoje + timedelta(days=2))

    for dia in (24, 25, 26):  # faltando 2 dias, 1 dia e no dia

        class Relogio(datetime):
            @classmethod
            def now(cls, tz=None, _dia=dia):  # noqa: ANN001, ANN206
                return datetime(2026, 11, _dia, 9, 0, tzinfo=tz)

        monkeypatch.setattr(tarefas, "datetime", Relogio)
        tarefas.lembretes_whatsapp()

    textos = wpp.para(maria.telefone)
    assert len(textos) == 2
    assert "vence em 2 dias, no dia 26/11" in textos[0]
    assert "vence hoje" in textos[1]
    assert sorted(_avisos(sessao, conta)) == ["antecipado", "no_dia"]


def test_aviso_de_amanha(sessao: Session, wpp: WhatsAppDeTeste, hoje: date) -> None:
    maria = _usuario(sessao)
    _conta(sessao, maria, hoje + timedelta(days=1), descricao=None)

    tarefas.lembretes_whatsapp()

    [texto] = wpp.para(maria.telefone)
    assert "'sem descrição' vence amanhã, no dia 25/11" in texto


def test_falha_no_envio_nao_registra_e_tenta_de_novo(
    sessao: Session, wpp: WhatsAppDeTeste, hoje: date
) -> None:
    maria = _usuario(sessao)
    conta = _conta(sessao, maria, hoje + timedelta(days=3))

    wpp.fora_do_ar = True
    assert tarefas.lembretes_whatsapp() == 0
    assert _avisos(sessao, conta) == []

    wpp.fora_do_ar = False
    tarefas.lembretes_whatsapp()

    assert len(wpp.para(maria.telefone)) == 1
    assert _avisos(sessao, conta) == ["antecipado"]


def test_quem_desligou_o_whatsapp_nao_recebe_antecipado(
    sessao: Session, wpp: WhatsAppDeTeste, hoje: date
) -> None:
    maria = _usuario(sessao, whatsapp=False)
    conta = _conta(sessao, maria, hoje + timedelta(days=3))

    tarefas.lembretes_whatsapp()

    assert wpp.para(maria.telefone) == []
    assert _avisos(sessao, conta) == []


def test_lembrete_continua_na_mesma_rotina_do_rf28() -> None:
    from app.nucleo.tarefas import fila

    agenda = fila.conf.beat_schedule["enviar-lembrete-whatsapp"]
    assert agenda["task"] == tarefas.lembretes_whatsapp.name
