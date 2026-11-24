"""Testes da exportação do resumo das finanças em PDF e CSV (RF38)."""

import csv
import io
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modulos.contas.modelos import Conta
from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import criar_token
from app.modulos.resumo import exportacao
from app.modulos.resumo.mensagens import Message
from app.modulos.transacoes.modelos import Transacao

URL = "/api/v1/resumo/exportar"


def _registro(
    sessao: Session,
    usuario: Usuario,
    dia: date,
    valor: str,
    tipo: str = "saida",
    descricao: str | None = "Mercado",
    origem: str = "manual",
) -> None:
    sessao.add(
        Transacao(
            usuario_id=usuario.id,
            tipo=tipo,
            valor=Decimal(valor),
            data=dia,
            descricao=descricao,
            origem=origem,
        )
    )
    sessao.flush()


def _conta(
    sessao: Session, usuario: Usuario, dia: date, valor: str, paga: bool = False
) -> None:
    sessao.add(
        Conta(
            usuario_id=usuario.id,
            vencimento_em=dia,
            valor=Decimal(valor),
            descricao="Luz",
            pagamento_em=datetime(2026, 10, 1, 12, 0) if paga else None,
        )
    )
    sessao.flush()


@pytest.fixture
def outubro(sessao: Session, usuario: Usuario) -> Usuario:
    """Outubro de 2026: salário, dois gastos, um automático e duas contas."""
    _registro(sessao, usuario, date(2026, 10, 5), "3300.00", "entrada", "Salário")
    _registro(sessao, usuario, date(2026, 10, 7), "250.40")
    _registro(sessao, usuario, date(2026, 10, 9), "1234.56", descricao=None)
    _registro(
        sessao, usuario, date(2026, 10, 10), "900.00", "saida", "Aluguel", "recorrente"
    )
    _registro(sessao, usuario, date(2026, 11, 1), "99.00", descricao="Fora do mês")
    _conta(sessao, usuario, date(2026, 10, 15), "120.00", paga=True)
    _conta(sessao, usuario, date(2026, 10, 25), "80.00")
    return usuario


def _linhas_csv(conteudo: bytes) -> list[list[str]]:
    texto = conteudo.decode("utf-8")
    assert texto.startswith("﻿")
    return list(csv.reader(io.StringIO(texto.removeprefix("﻿")), delimiter=";"))


def test_csv_traz_totais_categorias_registros_e_contas(
    outubro: Usuario, cliente_logado: TestClient
) -> None:
    resposta = cliente_logado.get(URL, params={"mes": "2026-10", "formato": "csv"})

    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/csv")
    assert (
        resposta.headers["content-disposition"]
        == 'attachment; filename="vero-resumo-2026-10.csv"'
    )
    linhas = _linhas_csv(resposta.content)
    assert linhas[0] == ["Resumo das suas finanças", "outubro de 2026"]
    totais = dict(linhas[4:8])
    assert totais["Dinheiro que entrou"] == "3300,00"
    assert totais["Gastos"] == "2384,96"
    assert totais["Contas do mês"] == "200,00"
    assert totais["Dinheiro disponível"] == "715,04"

    registros = linhas[linhas.index(["O que entrou e saiu"]) + 2 :]
    registros = registros[: registros.index([])]
    assert registros == [
        ["05/10/2026", "Entrou", "Salário", "Sem categoria", "3300,00"],
        ["07/10/2026", "Gastou", "Mercado", "Sem categoria", "250,40"],
        ["09/10/2026", "Gastou", "Sem descrição", "Sem categoria", "1234,56"],
        ["10/10/2026", "Gastou", "Aluguel (automático)", "Sem categoria", "900,00"],
    ]
    contas = linhas[linhas.index(["Contas do mês"]) + 2 :]
    assert contas == [
        ["15/10/2026", "Luz", "120,00", "Paga"],
        ["25/10/2026", "Luz", "80,00", "Atrasada"],
    ]


def test_csv_mostra_o_nome_da_categoria(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    from sqlalchemy import text

    categoria_id = sessao.execute(
        text(
            'INSERT INTO "tblCategoria" ("noCategoria") VALUES (\'Farmácia\') '
            'RETURNING "idCategoria"'
        )
    ).scalar_one()
    sessao.add(
        Transacao(
            usuario_id=usuario.id,
            tipo="saida",
            valor=Decimal("45.00"),
            data=date(2026, 10, 3),
            descricao="Remédio",
            categoria_id=categoria_id,
            origem="manual",
        )
    )
    sessao.flush()

    linhas = _linhas_csv(
        cliente_logado.get(URL, params={"mes": "2026-10", "formato": "csv"}).content
    )

    assert ["03/10/2026", "Gastou", "Remédio", "Farmácia", "45,00"] in linhas
    assert ["Farmácia", "45,00"] in linhas


def test_pdf_para_baixar(outubro: Usuario, cliente_logado: TestClient) -> None:
    resposta = cliente_logado.get(URL, params={"mes": "2026-10", "formato": "pdf"})

    assert resposta.status_code == 200
    assert resposta.headers["content-type"] == "application/pdf"
    assert (
        resposta.headers["content-disposition"]
        == 'attachment; filename="vero-resumo-2026-10.pdf"'
    )
    assert resposta.content.startswith(b"%PDF")


def test_pdf_e_o_formato_padrao(cliente_logado: TestClient) -> None:
    resposta = cliente_logado.get(URL, params={"mes": "2026-10"})

    assert resposta.headers["content-type"] == "application/pdf"


def test_pdf_traz_o_mes_os_totais_e_os_registros(
    sessao: Session, outubro: Usuario
) -> None:
    resumo = exportacao.montar(sessao, outubro.id, "2026-10")

    pdf = exportacao.gerar_pdf(resumo, comprimir=False)

    for trecho in (
        b"Resumo das suas finan",
        b"Outubro de 2026",
        b"Dinheiro dispon",
        b"R$ 715,04",
        b"R$ 3.300,00",
        b"Aluguel \\(autom",
        b"Atrasada",
    ):
        assert trecho in pdf, trecho


def test_mes_sem_nada_gera_o_arquivo_com_aviso(
    sessao: Session, usuario: Usuario, cliente_logado: TestClient
) -> None:
    resumo = exportacao.montar(sessao, usuario.id, "2026-10")
    pdf = exportacao.gerar_pdf(resumo, comprimir=False)
    linhas = _linhas_csv(
        cliente_logado.get(URL, params={"mes": "2026-10", "formato": "csv"}).content
    )

    assert b"Nada registrado neste m" in pdf
    assert dict(linhas[4:8])["Dinheiro disponível"] == "0,00"


def test_sem_mes_usa_o_mes_atual(cliente_logado: TestClient) -> None:
    resposta = cliente_logado.get(URL, params={"formato": "csv"})

    atual = exportacao.mes_atual()
    assert f'vero-resumo-{atual}.csv"' in resposta.headers["content-disposition"]


def test_nao_traz_registros_de_outra_pessoa(
    sessao: Session, outubro: Usuario, cliente: TestClient
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
    token = criar_token(outro.id, "pin", timedelta(hours=1))

    resposta = cliente.get(
        URL,
        params={"mes": "2026-10", "formato": "csv"},
        headers={"Authorization": f"Bearer {token}"},
    )

    linhas = _linhas_csv(resposta.content)
    assert dict(linhas[4:8])["Dinheiro que entrou"] == "0,00"
    assert not any("Salário" in c for linha in linhas for c in linha)


@pytest.mark.parametrize("mes", ["2026-13", "2026-1", "outubro", "26-10"])
def test_mes_que_nao_esta_certo_retorna_422(
    cliente_logado: TestClient, mes: str
) -> None:
    resposta = cliente_logado.get(URL, params={"mes": mes})

    assert resposta.status_code == 422
    assert resposta.json()["detail"] == Message.MES_INVALIDO.message


def test_formato_que_nao_existe_retorna_422(cliente_logado: TestClient) -> None:
    resposta = cliente_logado.get(URL, params={"mes": "2026-10", "formato": "docx"})

    assert resposta.status_code == 422
    assert resposta.json()["detail"] == Message.FORMATO_INVALIDO.message


def test_sem_entrar_na_conta_retorna_401(cliente: TestClient) -> None:
    assert cliente.get(URL, params={"mes": "2026-10"}).status_code == 401


@pytest.mark.parametrize(
    ("valor", "leitura", "planilha"),
    [
        ("0", "R$ 0,00", "0,00"),
        ("1234.5", "R$ 1.234,50", "1234,50"),
        ("-80", "R$ -80,00", "-80,00"),
    ],
)
def test_numeros_do_jeito_brasileiro(valor: str, leitura: str, planilha: str) -> None:
    assert exportacao.moeda(Decimal(valor)) == leitura
    assert exportacao.numero_planilha(Decimal(valor)) == planilha
