"""RF24: resumo semanal e mensal no WhatsApp, que a pessoa pode desligar."""

import uuid
from contextlib import nullcontext
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.modulos.contas.modelos import Categoria
from app.modulos.identidade.modelos import Usuario
from app.modulos.resumo import servico as servico_resumo
from app.modulos.resumo import tarefas as tarefas_resumo
from app.modulos.resumo.servico import (
    Periodo,
    comando_resumo,
    datas_do_periodo,
    montar_resumo,
    texto_resumo,
)
from app.modulos.transacoes.modelos import Transacao
from app.nucleo.tarefas import fila
from tests.test_assistente_rf12_rf15 import ambiente_assistente  # noqa: F401

# Segunda-feira: o resumo semanal fala de 16/11 a 22/11
SEGUNDA = date(2026, 11, 23)


@pytest.fixture
def categorias(sessao: Session) -> dict[str, int]:
    ids = {}
    for nome in ["Alimentação", "Saúde", "Moradia", "Lazer"]:
        categoria = Categoria(nome=nome)
        sessao.add(categoria)
        sessao.flush()
        ids[nome] = categoria.id
    return ids


def _lancar(
    sessao: Session,
    usuario: Usuario,
    valor: str,
    dia: date,
    tipo: str = "saida",
    categoria_id: int | None = None,
) -> None:
    sessao.add(
        Transacao(
            usuario_id=usuario.id,
            tipo=tipo,
            valor=Decimal(valor),
            data=dia,
            origem="manual",
            categoria_id=categoria_id,
        )
    )
    sessao.flush()


@pytest.fixture
def semana_com_gastos(sessao, usuario, categorias):
    _lancar(sessao, usuario, "2000.00", date(2026, 11, 5), "entrada")
    _lancar(
        sessao,
        usuario,
        "200.00",
        date(2026, 11, 16),
        categoria_id=categorias["Alimentação"],
    )
    _lancar(
        sessao,
        usuario,
        "50.00",
        date(2026, 11, 20),
        categoria_id=categorias["Alimentação"],
    )
    _lancar(
        sessao, usuario, "120.00", date(2026, 11, 18), categoria_id=categorias["Saúde"]
    )
    _lancar(
        sessao, usuario, "90.00", date(2026, 11, 22), categoria_id=categorias["Moradia"]
    )
    _lancar(
        sessao, usuario, "10.00", date(2026, 11, 21), categoria_id=categorias["Lazer"]
    )
    # Sem categoria (ex.: veio do assistente): conta no total, não na lista
    _lancar(sessao, usuario, "30.00", date(2026, 11, 19))
    # Fora da semana: só entra no saldo do mês
    _lancar(
        sessao, usuario, "500.00", date(2026, 11, 10), categoria_id=categorias["Lazer"]
    )
    # Hoje: fica para o próximo resumo
    _lancar(sessao, usuario, "999.00", SEGUNDA, categoria_id=categorias["Lazer"])
    return usuario


def test_datas_do_periodo():
    assert datas_do_periodo(Periodo.SEMANAL, SEGUNDA) == (
        date(2026, 11, 16),
        date(2026, 11, 22),
    )
    assert datas_do_periodo(Periodo.MENSAL, date(2026, 12, 1)) == (
        date(2026, 11, 1),
        date(2026, 11, 30),
    )
    assert datas_do_periodo(Periodo.MENSAL, date(2027, 1, 1)) == (
        date(2026, 12, 1),
        date(2026, 12, 31),
    )


def test_resumo_semanal_curto_com_maiores_categorias(sessao, semana_com_gastos):
    resumo = montar_resumo(sessao, semana_com_gastos.id, Periodo.SEMANAL, SEGUNDA)

    assert resumo.gastos == Decimal("500.00")
    assert resumo.categorias == [
        ("Alimentação", Decimal("250.00")),
        ("Saúde", Decimal("120.00")),
        ("Moradia", Decimal("90.00")),
    ]
    # 2000 de entrada - (500 da semana + 500 + 999 do resto do mês)
    assert resumo.saldo_mes == Decimal("1.00")

    texto = texto_resumo(resumo)
    assert texto.startswith("📊 *Seu resumo da semana* (16/11 a 22/11)")
    assert "Nos últimos 7 dias, você gastou *R$ 500,00*." in texto
    assert (
        "Onde mais gastou: Alimentação (R$ 250,00), Saúde (R$ 120,00) "
        "e Moradia (R$ 90,00)." in texto
    )
    assert "Em novembro, ainda restam *R$ 1,00*." in texto
    assert "responda *parar resumo*" in texto
    assert "Lazer" not in texto


def test_resumo_mensal_com_saldo_negativo(sessao, usuario, categorias):
    _lancar(sessao, usuario, "100.00", date(2026, 10, 2), "entrada")
    _lancar(
        sessao,
        usuario,
        "1350.50",
        date(2026, 10, 15),
        categoria_id=categorias["Moradia"],
    )

    resumo = montar_resumo(sessao, usuario.id, Periodo.MENSAL, date(2026, 11, 1))
    texto = texto_resumo(resumo)

    assert texto.startswith("📊 *Seu resumo de outubro*")
    assert "Em outubro, você gastou *R$ 1.350,50*." in texto
    assert "Onde mais gastou: Moradia (R$ 1.350,50)." in texto
    assert "Em outubro, os gastos passaram as entradas em *R$ 1.250,50*." in texto


def test_sem_gastos_nao_manda_resumo(sessao, usuario):
    _lancar(sessao, usuario, "1500.00", date(2026, 11, 17), "entrada")

    assert montar_resumo(sessao, usuario.id, Periodo.SEMANAL, SEGUNDA) is None


@pytest.fixture
def envio(monkeypatch, sessao):
    enviadas = []

    class WhatsAppTeste:
        def enviar(self, destinatario, assunto, texto):
            enviadas.append((destinatario, texto))

    monkeypatch.setattr(tarefas_resumo, "obter_whatsapp", WhatsAppTeste)
    monkeypatch.setattr(tarefas_resumo, "SessaoLocal", lambda: nullcontext(sessao))
    monkeypatch.setattr(servico_resumo, "SessaoLocal", lambda: nullcontext(sessao))
    return enviadas


def _meus(enviadas, usuario):
    return [t for d, t in enviadas if d == f"{usuario.telefone}@s.whatsapp.net"]


def test_envia_resumo_semanal(semana_com_gastos, envio):
    tarefas_resumo.enviar_resumos(Periodo.SEMANAL, SEGUNDA)

    textos = _meus(envio, semana_com_gastos)
    assert len(textos) == 1
    assert "você gastou *R$ 500,00*" in textos[0]


@pytest.mark.parametrize("campo", ["resumo_ativo", "whatsapp_ativo"])
def test_nao_envia_para_quem_desligou(sessao, semana_com_gastos, envio, campo):
    setattr(semana_com_gastos, campo, False)
    sessao.flush()

    tarefas_resumo.enviar_resumos(Periodo.SEMANAL, SEGUNDA)

    assert _meus(envio, semana_com_gastos) == []


def test_falha_com_uma_pessoa_nao_para_as_outras(
    sessao, semana_com_gastos, envio, monkeypatch
):
    original = tarefas_resumo.montar_resumo
    outro = Usuario(
        id=uuid.uuid4(),
        nome="José",
        hash_telefone=uuid.uuid4().hex,
        email=f"jose{uuid.uuid4().hex[:8]}@vero.com",
        hash_pin="x",
        tentativas=0,
    )
    outro.telefone = "55618" + uuid.uuid4().hex[:8]
    sessao.add(outro)
    sessao.flush()
    _lancar(sessao, outro, "10.00", date(2026, 11, 17))

    def montar(sessao_, usuario_id, periodo, hoje):
        if usuario_id == outro.id:
            raise RuntimeError("falhou")
        return original(sessao_, usuario_id, periodo, hoje)

    monkeypatch.setattr(tarefas_resumo, "montar_resumo", montar)

    tarefas_resumo.enviar_resumos(Periodo.SEMANAL, SEGUNDA)

    assert len(_meus(envio, semana_com_gastos)) == 1


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("parar resumo", False),
        ("Parar o resumo!", False),
        ("NÃO QUERO MAIS RESUMO", False),
        ("voltar resumo", True),
        ("Quero o resumo", True),
        ("parar", None),
        ("gastei 35 na farmácia", None),
    ],
)
def test_reconhece_comando(texto, esperado):
    assert comando_resumo(texto) is esperado


def test_parar_e_voltar_resumo_grava_preferencia(sessao, usuario, envio):
    resposta = servico_resumo.tratar_comando(usuario.id, "parar resumo")

    assert "não vou mais mandar o resumo" in resposta
    assert "*voltar resumo*" in resposta
    sessao.refresh(usuario)
    assert usuario.resumo_ativo is False

    servico_resumo.tratar_comando(usuario.id, "voltar resumo")
    sessao.refresh(usuario)
    assert usuario.resumo_ativo is True

    assert servico_resumo.tratar_comando(usuario.id, "oi") is None


def test_assistente_atende_parar_resumo_antes_de_tudo(
    ambiente_assistente,  # noqa: F811
    monkeypatch,
):
    sessao, telefone, enviadas, registrar, enviar = ambiente_assistente
    chamadas = []

    def tratar(usuario_id, texto):
        chamadas.append(texto)
        return "desligado" if texto == "parar resumo" else None

    monkeypatch.setattr(servico_resumo, "tratar_comando", tratar)

    enviar("gastei 35 na farmácia")
    enviar("parar resumo")

    assert enviadas[-1] == "desligado"
    # A confirmação pendente continua lá
    assert sessao.obter_pendencia(telefone)[0].valor == 3500
    assert registrar.call_count == 0


def test_agenda_do_celery():
    agenda = {item["task"] for item in fila.conf.beat_schedule.values()}
    assert {"resumo.semanal", "resumo.mensal"} <= agenda
