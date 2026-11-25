"""Testes do lembrete no WhatsApp no dia do vencimento (RF28)."""

import contextlib
import logging
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integracoes.wpp import WhatsAppFalso, obter_whatsapp
from app.modulos.contas import servico as servico_contas
from app.modulos.contas.modelos import Conta
from app.modulos.identidade.modelos import Usuario
from app.modulos.transacoes import servico, tarefas
from app.modulos.transacoes.modelos import Transacao


@dataclass
class Mensagem:
    destinatario: str
    assunto: str
    texto: str


class WhatsAppDeTeste:
    """Guarda as mensagens em vez de enviar."""

    def __init__(self) -> None:
        self.mensagens: list[Mensagem] = []

    def enviar(self, destinatario: str, assunto: str, texto: str) -> None:
        self.mensagens.append(Mensagem(destinatario, assunto, texto))

    def para(self, telefone: str) -> list[Mensagem]:
        return [m for m in self.mensagens if m.destinatario.startswith(f"{telefone}@")]


@pytest.fixture
def wpp(sessao: Session, monkeypatch: pytest.MonkeyPatch) -> WhatsAppDeTeste:
    """A tarefa usa a sessão do teste e o WhatsApp de teste."""
    falso = WhatsAppDeTeste()
    monkeypatch.setattr(tarefas, "SessaoLocal", lambda: contextlib.nullcontext(sessao))
    monkeypatch.setattr(tarefas, "obter_whatsapp", lambda: falso)
    return falso


def _hoje() -> date:
    return datetime.now(servico.FUSO_BRASILIA).date()


def _usuario(
    sessao: Session, telefone: str | None, whatsapp_ativo: bool = True
) -> Usuario:
    u = Usuario(
        id=uuid.uuid4(),
        nome="Maria",
        hash_telefone=uuid.uuid4().hex,
        email=f"maria{uuid.uuid4().hex[:8]}@vero.com",
        hash_pin="x",
        tentativas=0,
        telefone=telefone,
        whatsapp_ativo=whatsapp_ativo,
    )
    sessao.add(u)
    sessao.flush()
    return u


def _telefone() -> str:
    return "5561" + uuid.uuid4().hex[:9].translate(str.maketrans("abcdef", "123456"))


def _conta(
    sessao: Session,
    usuario: Usuario,
    vencimento: date,
    descricao: str | None = "Conta de Água",
    valor: str = "1250.50",
    paga: bool = False,
) -> Conta:
    conta = Conta(
        usuario_id=usuario.id,
        vencimento_em=vencimento,
        valor=Decimal(valor),
        descricao=descricao,
        pagamento_em=datetime.now(servico.FUSO_BRASILIA) if paga else None,
    )
    sessao.add(conta)
    sessao.flush()
    return conta


def test_texto_do_lembrete_traz_descricao_e_valor_em_reais() -> None:
    conta = Conta(descricao="Energia elétrica", valor=Decimal("1250.50"))

    texto = tarefas._montar_texto_lembrete(conta)

    assert "'Energia elétrica'" in texto
    assert "R$ 1.250,50" in texto


def test_texto_do_lembrete_sem_descricao() -> None:
    texto = tarefas._montar_texto_lembrete(Conta(valor=Decimal("50.00")))

    assert "'sem descrição'" in texto
    assert "R$ 50,00" in texto


def test_busca_so_contas_de_hoje_nao_pagas(sessao: Session) -> None:
    maria = _usuario(sessao, _telefone())
    hoje = _hoje()
    de_hoje = _conta(sessao, maria, hoje)
    _conta(sessao, maria, hoje, paga=True)
    _conta(sessao, maria, hoje + timedelta(days=1))

    contas = servico_contas.contas_em_aberto_entre(sessao, hoje, hoje)

    assert [c.id for c in contas if c.usuario_id == maria.id] == [de_hoje.id]


def test_envia_lembrete_para_quem_tem_telefone(
    sessao: Session, wpp: WhatsAppDeTeste
) -> None:
    telefone = _telefone()
    maria = _usuario(sessao, telefone)
    _conta(sessao, maria, _hoje())

    assert tarefas.lembretes_whatsapp() >= 1

    [mensagem] = wpp.para(telefone)
    assert mensagem.destinatario == f"{telefone}@s.whatsapp.net"
    assert mensagem.assunto == "Lembrete de vencimento"
    assert "Conta de Água" in mensagem.texto


def test_lembrete_nao_lanca_gasto(sessao: Session, wpp: WhatsAppDeTeste) -> None:
    """O gasto só entra no saldo quando a pessoa marca a conta como paga (RF30)."""
    maria = _usuario(sessao, _telefone())
    _conta(sessao, maria, _hoje())

    tarefas.lembretes_whatsapp()

    transacoes = sessao.scalars(
        select(Transacao).where(Transacao.usuario_id == maria.id)
    ).all()
    assert transacoes == []


def test_quem_nao_tem_telefone_e_pulado_sem_parar_os_demais(
    sessao: Session, wpp: WhatsAppDeTeste
) -> None:
    sem_telefone = _usuario(sessao, None)
    telefone = _telefone()
    com_telefone = _usuario(sessao, telefone)
    _conta(sessao, sem_telefone, _hoje())
    _conta(sessao, com_telefone, _hoje())

    tarefas.lembretes_whatsapp()

    assert len(wpp.para(telefone)) == 1
    assert not wpp.para("None")


def test_quem_desligou_o_whatsapp_nao_recebe(
    sessao: Session, wpp: WhatsAppDeTeste
) -> None:
    telefone = _telefone()
    maria = _usuario(sessao, telefone, whatsapp_ativo=False)
    _conta(sessao, maria, _hoje())

    tarefas.lembretes_whatsapp()

    assert wpp.para(telefone) == []


def test_falha_no_envio_nao_interrompe_os_demais(
    sessao: Session, wpp: WhatsAppDeTeste, monkeypatch: pytest.MonkeyPatch
) -> None:
    falha, ok = _telefone(), _telefone()
    _conta(sessao, _usuario(sessao, falha), _hoje())
    _conta(sessao, _usuario(sessao, ok), _hoje())
    enviar = wpp.enviar

    def enviar_ou_falhar(destinatario: str, assunto: str, texto: str) -> None:
        if destinatario.startswith(f"{falha}@"):
            raise RuntimeError("fora do ar")
        enviar(destinatario, assunto, texto)

    monkeypatch.setattr(wpp, "enviar", enviar_ou_falhar)

    tarefas.lembretes_whatsapp()

    assert len(wpp.para(ok)) == 1


def test_adaptador_falso_so_registra_no_log(caplog: pytest.LogCaptureFixture) -> None:
    wpp = obter_whatsapp()
    assert isinstance(wpp, WhatsAppFalso)

    with caplog.at_level(logging.WARNING):
        wpp.enviar("5561999990000@s.whatsapp.net", "Assunto", "Texto")

    assert "não enviado" in caplog.text
