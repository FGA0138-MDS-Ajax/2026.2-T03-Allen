"""Testes do lançamento automático dos gastos fixos (RF18)."""

import contextlib
import uuid
from datetime import date, datetime
from decimal import Decimal

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modulos.contas.modelos import Conta
from app.modulos.identidade.modelos import Usuario
from app.modulos.transacoes import servico, tarefas
from app.modulos.transacoes.modelos import Transacao
from app.nucleo import eventos

HOJE = date(2026, 3, 15)


@pytest.fixture(autouse=True)
def valkey_falso(monkeypatch: pytest.MonkeyPatch) -> None:
    """Os avisos ao app (RF17) vão para um Valkey em memória."""
    monkeypatch.setattr(eventos, "cliente", fakeredis.FakeRedis())


def _conta(
    sessao: Session,
    usuario: Usuario,
    vencimento: date,
    recorrente: bool = True,
    valor: str = "120.00",
) -> Conta:
    conta = Conta(
        usuario_id=usuario.id,
        vencimento_em=vencimento,
        valor=Decimal(valor),
        descricao="Aluguel",
        recorrente=recorrente,
    )
    sessao.add(conta)
    sessao.flush()
    return conta


def _transacoes(sessao: Session, usuario: Usuario) -> list[Transacao]:
    return list(
        sessao.scalars(
            select(Transacao)
            .where(Transacao.usuario_id == usuario.id)
            .order_by(Transacao.data)
        )
    )


def _contas(sessao: Session, usuario: Usuario) -> list[Conta]:
    return list(
        sessao.scalars(
            select(Conta)
            .where(Conta.usuario_id == usuario.id)
            .order_by(Conta.vencimento_em)
        )
    )


def test_gasto_fixo_vencido_vira_saida_automatica_na_data_do_vencimento(
    sessao: Session, usuario: Usuario
) -> None:
    conta = _conta(sessao, usuario, HOJE)

    assert servico.lancar_gastos_fixos(sessao, HOJE) == 1

    [transacao] = _transacoes(sessao, usuario)
    assert transacao.tipo == "saida"
    assert transacao.origem == "recorrente"
    assert transacao.valor == Decimal("120.00")
    assert transacao.data == HOJE
    assert transacao.descricao == "Aluguel"
    assert transacao.conta_id == conta.id
    assert conta.pagamento_em is not None


def test_lancamento_cria_a_conta_do_mes_seguinte(
    sessao: Session, usuario: Usuario
) -> None:
    conta = _conta(sessao, usuario, HOJE)

    servico.lancar_gastos_fixos(sessao, HOJE)

    _, proxima = _contas(sessao, usuario)
    assert proxima.vencimento_em == date(2026, 4, 15)
    assert proxima.recorrente is True
    assert proxima.id_conta_origem == conta.id
    assert proxima.pagamento_em is None


def test_rodar_duas_vezes_nao_duplica_o_lancamento(
    sessao: Session, usuario: Usuario
) -> None:
    _conta(sessao, usuario, HOJE)

    assert servico.lancar_gastos_fixos(sessao, HOJE) == 1
    assert servico.lancar_gastos_fixos(sessao, HOJE) == 0

    assert len(_transacoes(sessao, usuario)) == 1
    assert len(_contas(sessao, usuario)) == 2


def test_banco_recusa_dois_lancamentos_da_mesma_conta(
    sessao: Session, usuario: Usuario
) -> None:
    conta = _conta(sessao, usuario, HOJE)
    servico.lancar_gastos_fixos(sessao, HOJE)

    duplicada = Transacao(
        usuario_id=usuario.id,
        tipo="saida",
        valor=conta.valor,
        data=HOJE,
        origem="recorrente",
        conta_id=conta.id,
    )
    sessao.add(duplicada)
    with pytest.raises(IntegrityError):
        sessao.flush()


def test_nao_lanca_antes_do_vencimento(sessao: Session, usuario: Usuario) -> None:
    _conta(sessao, usuario, date(2026, 3, 16))

    assert servico.lancar_gastos_fixos(sessao, HOJE) == 0
    assert _transacoes(sessao, usuario) == []


def test_nao_lanca_conta_que_nao_e_fixa(sessao: Session, usuario: Usuario) -> None:
    conta = _conta(sessao, usuario, HOJE, recorrente=False)

    assert servico.lancar_gastos_fixos(sessao, HOJE) == 0
    assert conta.pagamento_em is None


def test_nao_lanca_gasto_fixo_que_o_usuario_ja_pagou(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    conta = _conta(sessao, usuario, HOJE)
    cliente_logado.patch(f"/api/v1/contas/{conta.id}/pagamento", json={"paga": True})

    assert servico.lancar_gastos_fixos(sessao, HOJE) == 0


def test_meses_atrasados_sao_lancados_um_por_mes(
    sessao: Session, usuario: Usuario
) -> None:
    _conta(sessao, usuario, date(2026, 1, 10))

    assert servico.lancar_gastos_fixos(sessao, HOJE) == 3

    datas = [t.data for t in _transacoes(sessao, usuario)]
    assert datas == [date(2026, 1, 10), date(2026, 2, 10), date(2026, 3, 10)]
    assert _contas(sessao, usuario)[-1].vencimento_em == date(2026, 4, 10)


def test_lanca_os_gastos_fixos_de_cada_usuario(
    sessao: Session, usuario: Usuario
) -> None:
    outro = Usuario(
        id=uuid.uuid4(),
        nome="José",
        hash_telefone=uuid.uuid4().hex,
        email=f"jose{uuid.uuid4().hex[:8]}@vero.com",
        hash_pin="x",
        tentativas=0,
    )
    sessao.add(outro)
    sessao.flush()
    _conta(sessao, usuario, HOJE)
    _conta(sessao, outro, HOJE, valor="80.00")

    assert servico.lancar_gastos_fixos(sessao, HOJE) == 2
    assert [t.valor for t in _transacoes(sessao, outro)] == [Decimal("80.00")]


def test_lancamento_avisa_o_app_em_tempo_real(
    sessao: Session, usuario: Usuario, monkeypatch: pytest.MonkeyPatch
) -> None:
    avisos = []
    monkeypatch.setattr(eventos, "publicar", lambda *aviso: avisos.append(aviso))
    _conta(sessao, usuario, HOJE)

    servico.lancar_gastos_fixos(sessao, HOJE)

    [(usuario_id, tipo, dados)] = avisos
    assert usuario_id == usuario.id
    assert tipo == eventos.TipoEvento.TRANSACAO_CRIADA
    assert dados["origem"] == "recorrente"


def test_historico_mostra_o_lancamento_como_automatico(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    _conta(sessao, usuario, HOJE)
    servico.lancar_gastos_fixos(sessao, HOJE)

    [item] = cliente_logado.get("/api/v1/transacoes").json()

    assert item["origem"] == "recorrente"
    assert item["tipo"] == "saida"


def test_lancamento_automatico_editado_continua_automatico(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    _conta(sessao, usuario, HOJE)
    servico.lancar_gastos_fixos(sessao, HOJE)
    [transacao] = _transacoes(sessao, usuario)

    resposta = cliente_logado.patch(
        f"/api/v1/transacoes/{transacao.id}", json={"valor": "130.00"}
    )

    assert resposta.status_code == 200
    assert resposta.json()["valor"] == "130.00"
    assert resposta.json()["origem"] == "recorrente"


def test_lancamento_automatico_excluido_nao_volta(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    _conta(sessao, usuario, HOJE)
    servico.lancar_gastos_fixos(sessao, HOJE)
    [transacao] = _transacoes(sessao, usuario)

    resposta = cliente_logado.delete(f"/api/v1/transacoes/{transacao.id}")

    assert resposta.status_code == 204
    assert servico.lancar_gastos_fixos(sessao, HOJE) == 0
    assert _transacoes(sessao, usuario) == []


def test_desfazer_o_pagamento_nao_lanca_de_novo(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    conta = _conta(sessao, usuario, HOJE)
    servico.lancar_gastos_fixos(sessao, HOJE)
    cliente_logado.patch(f"/api/v1/contas/{conta.id}/pagamento", json={"paga": False})

    assert servico.lancar_gastos_fixos(sessao, HOJE) == 0
    assert len(_transacoes(sessao, usuario)) == 1


def test_tarefa_do_celery_lanca_com_a_data_de_hoje(
    sessao: Session, usuario: Usuario, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tarefas, "SessaoLocal", lambda: contextlib.nullcontext(sessao))
    _conta(sessao, usuario, datetime.now(servico.FUSO_BRASILIA).date())

    assert tarefas.lancar_gastos_fixos() == 1


def test_rotina_diaria_esta_agendada_no_fuso_de_brasilia() -> None:
    from app.nucleo.tarefas import fila

    agenda = fila.conf.beat_schedule["lancar-gastos-fixos"]
    assert agenda["task"] == tarefas.lancar_gastos_fixos.name
    assert fila.conf.timezone == "America/Sao_Paulo"


def test_toda_rotina_agendada_aponta_para_uma_tarefa_registrada() -> None:
    """O Beat agenda pelo nome: nome errado e a rotina nunca roda."""
    from app.nucleo.tarefas import fila

    registradas = set(fila.tasks.keys())
    for nome, agenda in fila.conf.beat_schedule.items():
        assert agenda["task"] in registradas, nome
