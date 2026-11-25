"""Testes da compra parcelada (RF37)."""

from datetime import date
from decimal import Decimal

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modulos.contas.mensagens import Message
from app.modulos.contas.parcelas import datas_das_parcelas, dividir_valor
from app.modulos.identidade.modelos import Usuario
from app.modulos.transacoes import servico as servico_transacoes
from app.modulos.transacoes.modelos import Transacao
from app.nucleo import eventos


@pytest.fixture(autouse=True)
def hoje_no_dia_da_compra(fixar_hoje_contas) -> None:
    # As compras dos testes são de 14/11/2026 (validação de vencimento, #121)
    fixar_hoje_contas(date(2026, 11, 14))


@pytest.fixture(autouse=True)
def valkey_falso(monkeypatch: pytest.MonkeyPatch) -> None:
    """Os avisos ao app (RF17) vão para um Valkey em memória."""
    monkeypatch.setattr(eventos, "cliente", fakeredis.FakeRedis())


def _comprar(
    cliente: TestClient,
    parcelas: int = 3,
    valor: str = "1000.00",
    compra: str = "2026-11-14",
    descricao: str | None = "Geladeira",
):
    dados = {"vencimento_em": compra, "valor": valor, "parcelas": parcelas}
    if descricao is not None:
        dados["descricao"] = descricao
    return cliente.post("/api/v1/contas", json=dados)


def _parcelas(cliente: TestClient) -> list[dict]:
    return [c for c in cliente.get("/api/v1/contas").json() if c["total_parcelas"]]


# Regras de divisão e de datas


@pytest.mark.parametrize(
    ("total", "parcelas", "esperado"),
    [
        ("1000.00", 3, ["333.34", "333.33", "333.33"]),
        ("100.00", 4, ["25.00", "25.00", "25.00", "25.00"]),
        ("0.05", 2, ["0.03", "0.02"]),
        ("10.01", 2, ["5.01", "5.00"]),
    ],
)
def test_centavos_que_sobram_vao_na_primeira_parcela(
    total: str, parcelas: int, esperado: list[str]
) -> None:
    valores = dividir_valor(Decimal(total), parcelas)

    assert valores == [Decimal(v) for v in esperado]
    assert sum(valores) == Decimal(total)


def test_primeira_parcela_vence_no_mes_seguinte_ao_da_compra() -> None:
    assert datas_das_parcelas(date(2026, 11, 14), 3) == [
        date(2026, 12, 14),
        date(2027, 1, 14),
        date(2027, 2, 14),
    ]


def test_dia_da_compra_volta_depois_do_mes_curto() -> None:
    assert datas_das_parcelas(date(2026, 12, 31), 4) == [
        date(2027, 1, 31),
        date(2027, 2, 28),
        date(2027, 3, 31),
        date(2027, 4, 30),
    ]


# Cadastro pela API


def test_compra_parcelada_cria_uma_conta_por_mes(cliente_logado: TestClient) -> None:
    resposta = _comprar(cliente_logado)

    assert resposta.status_code == 201
    primeira = resposta.json()
    assert (primeira["parcela"], primeira["total_parcelas"]) == (1, 3)
    assert primeira["valor"] == "333.34"
    assert primeira["vencimento_em"] == "2026-12-14"

    parcelas = _parcelas(cliente_logado)
    assert [(p["parcela"], p["vencimento_em"], p["valor"]) for p in parcelas] == [
        (1, "2026-12-14", "333.34"),
        (2, "2027-01-14", "333.33"),
        (3, "2027-02-14", "333.33"),
    ]
    assert all(p["status"] == "a_vencer" for p in parcelas)
    assert all(p["descricao"] == "Geladeira" for p in parcelas)
    assert all(p["recorrente"] is False for p in parcelas)


def test_parcelas_ficam_ligadas_a_primeira(cliente_logado: TestClient) -> None:
    primeira = _comprar(cliente_logado).json()

    origens = [p["id_conta_origem"] for p in _parcelas(cliente_logado)]

    assert origens == [None, primeira["id"], primeira["id"]]


def test_conta_comum_continua_sem_parcela(cliente_logado: TestClient) -> None:
    resposta = cliente_logado.post(
        "/api/v1/contas", json={"vencimento_em": "2026-12-10", "valor": "80.00"}
    )

    assert resposta.status_code == 201
    assert resposta.json()["parcela"] is None
    assert resposta.json()["total_parcelas"] is None


@pytest.mark.parametrize("parcelas", [0, 1, 25])
def test_numero_de_parcelas_fora_do_limite_retorna_422(
    cliente_logado: TestClient, parcelas: int
) -> None:
    resposta = _comprar(cliente_logado, parcelas=parcelas)

    assert resposta.status_code == 422
    assert resposta.json()["erros"] == [
        {
            "campo": "parcelas",
            "mensagem": Message.PARCELAS_FORA_DO_LIMITE.message.format(
                minimo=2, maximo=24
            ),
        }
    ]


def test_compra_parcelada_nao_pode_ser_conta_fixa(cliente_logado: TestClient) -> None:
    resposta = cliente_logado.post(
        "/api/v1/contas",
        json={
            "vencimento_em": "2026-11-14",
            "valor": "300.00",
            "parcelas": 3,
            "recorrente": True,
        },
    )

    assert resposta.status_code == 422
    assert resposta.json()["erros"][0]["mensagem"] == Message.PARCELADA_E_FIXA.message


def test_valor_menor_que_um_centavo_por_parcela_retorna_422(
    cliente_logado: TestClient,
) -> None:
    resposta = _comprar(cliente_logado, parcelas=3, valor="0.02")

    assert resposta.status_code == 422
    assert (
        resposta.json()["erros"][0]["mensagem"]
        == Message.VALOR_MENOR_QUE_PARCELAS.message
    )
    assert _parcelas(cliente_logado) == []


# Lançamento no extrato (lançamento automático do RF18)


def _transacoes(sessao: Session, usuario: Usuario) -> list[Transacao]:
    return list(
        sessao.scalars(
            select(Transacao)
            .where(Transacao.usuario_id == usuario.id)
            .order_by(Transacao.data)
        )
    )


def test_parcela_entra_no_extrato_no_vencimento_e_fica_paga(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    _comprar(cliente_logado)

    lancadas = servico_transacoes.lancar_gastos_fixos(sessao, date(2026, 12, 14))

    assert lancadas == 1
    [transacao] = _transacoes(sessao, usuario)
    assert transacao.descricao == "Geladeira (1/3)"
    assert transacao.valor == Decimal("333.34")
    assert transacao.data == date(2026, 12, 14)
    assert transacao.tipo == "saida"
    assert transacao.origem == "recorrente"
    status = [p["status"] for p in _parcelas(cliente_logado)]
    assert status == ["paga", "a_vencer", "a_vencer"]


def test_parcelas_futuras_nao_entram_antes_do_vencimento(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    _comprar(cliente_logado)

    assert servico_transacoes.lancar_gastos_fixos(sessao, date(2026, 12, 13)) == 0
    assert _transacoes(sessao, usuario) == []


def test_cada_parcela_entra_no_extrato_do_seu_mes_sem_duplicar(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    _comprar(cliente_logado)

    assert servico_transacoes.lancar_gastos_fixos(sessao, date(2027, 3, 1)) == 3
    assert servico_transacoes.lancar_gastos_fixos(sessao, date(2027, 3, 1)) == 0

    extrato = [(t.data, t.descricao, t.valor) for t in _transacoes(sessao, usuario)]
    assert extrato == [
        (date(2026, 12, 14), "Geladeira (1/3)", Decimal("333.34")),
        (date(2027, 1, 14), "Geladeira (2/3)", Decimal("333.33")),
        (date(2027, 2, 14), "Geladeira (3/3)", Decimal("333.33")),
    ]
    assert sum(valor for _, _, valor in extrato) == Decimal("1000.00")


def test_ultima_parcela_paga_nao_gera_mais_contas(
    sessao: Session, cliente_logado: TestClient
) -> None:
    _comprar(cliente_logado, parcelas=2, valor="200.00")

    servico_transacoes.lancar_gastos_fixos(sessao, date(2027, 6, 1))

    assert len(cliente_logado.get("/api/v1/contas").json()) == 2


def test_parcela_sem_descricao_aparece_como_parcela(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    _comprar(cliente_logado, parcelas=2, valor="50.00", descricao=None)

    servico_transacoes.lancar_gastos_fixos(sessao, date(2026, 12, 14))

    assert [t.descricao for t in _transacoes(sessao, usuario)] == ["Parcela (1/2)"]


def test_parcela_paga_a_mao_antes_do_vencimento_nao_entra_de_novo(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    primeira = _comprar(cliente_logado).json()
    cliente_logado.patch(
        f"/api/v1/contas/{primeira['id']}/pagamento", json={"paga": True}
    )

    servico_transacoes.lancar_gastos_fixos(sessao, date(2026, 12, 14))

    assert _transacoes(sessao, usuario) == []
