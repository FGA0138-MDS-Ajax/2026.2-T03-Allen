"""RF38: resumo das finanças de um mês para baixar em PDF ou CSV.

Traz os mesmos totais da tela inicial (entradas, gastos, contas e dinheiro disponível,
pelo `resumir_mes`), os gastos por categoria e a lista do que entrou, saiu e venceu no
mês. Os dados vêm dos serviços de transações e de contas: este módulo não lê tabelas.
"""

import csv
import io
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modulos.contas import servico as servico_contas
from app.modulos.contas.esquemas import StatusConta
from app.modulos.resumo.mensagens import Message
from app.modulos.resumo.servico import MESES
from app.modulos.transacoes import servico as servico_transacoes
from app.modulos.transacoes.esquemas import OrigemTransacao, TipoTransacao
from app.nucleo.mensagens import Message as MensagemComum
from app.nucleo.pdf import DocumentoPdf

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")
PADRAO_MES = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


class Formato(StrEnum):
    """Formatos de arquivo da exportação."""

    PDF = "pdf"
    CSV = "csv"


class MesInvalido(Exception):
    pass


@dataclass
class Registro:
    dia: date
    entrada: bool
    descricao: str
    categoria: str
    valor: Decimal


@dataclass
class ContaDoMes:
    dia_de_pagar: date
    descricao: str
    valor: Decimal
    situacao: str


@dataclass
class ResumoExportado:
    mes: date  # dia 1º do mês
    entradas: Decimal
    gastos: Decimal
    contas: Decimal
    disponivel: Decimal
    categorias: list[tuple[str, Decimal]]
    registros: list[Registro]
    contas_do_mes: list[ContaDoMes]
    gerado_em: date

    @property
    def nome_do_mes(self) -> str:
        return f"{MESES[self.mes.month - 1]} de {self.mes.year}"


def mes_atual() -> str:
    return datetime.now(FUSO_BRASILIA).strftime("%Y-%m")


def primeiro_e_ultimo_dia(mes: str) -> tuple[date, date]:
    """'2026-11' -> (01/11/2026, 30/11/2026). MesInvalido se não estiver no formato."""
    achado = PADRAO_MES.match(mes)
    if not achado:
        raise MesInvalido
    ano, numero = int(achado[1]), int(achado[2])
    inicio = date(ano, numero, 1)
    proximo = date(ano + 1, 1, 1) if numero == 12 else date(ano, numero + 1, 1)
    return inicio, date.fromordinal(proximo.toordinal() - 1)


_SITUACAO = {
    StatusConta.PAGA: Message.CONTA_PAGA,
    StatusConta.A_VENCER: Message.CONTA_A_PAGAR,
    StatusConta.EM_ATRASO: Message.CONTA_ATRASADA,
}


def montar(sessao: Session, usuario_id: uuid.UUID, mes: str) -> ResumoExportado:
    inicio, fim = primeiro_e_ultimo_dia(mes)
    totais = servico_transacoes.resumir_mes(sessao, usuario_id, mes)
    _, categorias = servico_transacoes.gastos_do_periodo(
        sessao, usuario_id, inicio, fim
    )
    nomes = servico_contas.nomes_das_categorias(sessao)

    registros = []
    for t in servico_transacoes.listar_do_periodo(sessao, usuario_id, inicio, fim):
        descricao = t.descricao or Message.SEM_DESCRICAO.message
        if t.origem == OrigemTransacao.RECORRENTE:
            descricao = Message.AUTOMATICO.message.format(descricao=descricao)
        registros.append(
            Registro(
                dia=t.data,
                entrada=t.tipo == TipoTransacao.ENTRADA,
                descricao=descricao,
                categoria=nomes.get(t.categoria_id, Message.SEM_CATEGORIA.message),
                valor=t.valor,
            )
        )

    contas = [
        ContaDoMes(
            dia_de_pagar=c.vencimento_em,
            descricao=c.descricao or Message.SEM_DESCRICAO.message,
            valor=c.valor,
            situacao=_SITUACAO[c.status].message,
        )
        for c in servico_contas.contas_do_periodo(sessao, usuario_id, inicio, fim)
    ]

    return ResumoExportado(
        mes=inicio,
        entradas=totais.entradas,
        gastos=totais.gastos,
        contas=totais.contas,
        disponivel=totais.saldo,
        categorias=categorias,
        registros=registros,
        contas_do_mes=contas,
        gerado_em=datetime.now(FUSO_BRASILIA).date(),
    )


def nome_do_arquivo(resumo: ResumoExportado, formato: Formato) -> str:
    return f"vero-resumo-{resumo.mes:%Y-%m}.{formato}"


# Números do jeito brasileiro


def moeda(valor: Decimal) -> str:
    """1234.5 -> 'R$ 1.234,50' (para ler)."""
    texto = f"R$ {valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def numero_planilha(valor: Decimal) -> str:
    """1234.5 -> '1234,50' (sem ponto de milhar, para a planilha somar)."""
    return f"{valor:.2f}".replace(".", ",")


def _totais(resumo: ResumoExportado) -> list[tuple[str, Decimal]]:
    return [
        (Message.TOTAL_ENTROU.message, resumo.entradas),
        (Message.TOTAL_GASTOU.message, resumo.gastos),
        (Message.TOTAL_CONTAS.message, resumo.contas),
        (Message.TOTAL_DISPONIVEL.message, resumo.disponivel),
    ]


def _tipo(registro: Registro) -> str:
    return (Message.TIPO_ENTRADA if registro.entrada else Message.TIPO_GASTO).message


# CSV


def gerar_csv(resumo: ResumoExportado) -> bytes:
    """Planilha com ponto e vírgula e vírgula decimal, como o Excel em português espera.
    O BOM no começo faz o Excel mostrar os acentos certos."""
    saida = io.StringIO()
    escrever = csv.writer(saida, delimiter=";", lineterminator="\r\n").writerow

    escrever([Message.TITULO.message, resumo.nome_do_mes])
    escrever(
        [
            MensagemComum.DOCUMENTO_GERADO_EM.message.format(
                data=f"{resumo.gerado_em:%d/%m/%Y}"
            )
        ]
    )
    escrever([])
    escrever([Message.SECAO_TOTAIS.message, Message.COLUNA_VALOR.message])
    for nome, valor in _totais(resumo):
        escrever([nome, numero_planilha(valor)])

    escrever([])
    escrever([Message.SECAO_CATEGORIAS.message, Message.COLUNA_VALOR.message])
    for nome, valor in resumo.categorias:
        escrever([nome, numero_planilha(valor)])

    escrever([])
    escrever([Message.SECAO_REGISTROS.message])
    escrever(
        [
            Message.COLUNA_DIA.message,
            Message.COLUNA_TIPO.message,
            Message.COLUNA_DESCRICAO.message,
            Message.COLUNA_CATEGORIA.message,
            Message.COLUNA_VALOR.message,
        ]
    )
    for r in resumo.registros:
        escrever(
            [
                f"{r.dia:%d/%m/%Y}",
                _tipo(r),
                r.descricao,
                r.categoria,
                numero_planilha(r.valor),
            ]
        )

    escrever([])
    escrever([Message.SECAO_CONTAS.message])
    escrever(
        [
            Message.COLUNA_DIA_DE_PAGAR.message,
            Message.COLUNA_DESCRICAO.message,
            Message.COLUNA_VALOR.message,
            Message.COLUNA_SITUACAO.message,
        ]
    )
    for c in resumo.contas_do_mes:
        escrever(
            [
                f"{c.dia_de_pagar:%d/%m/%Y}",
                c.descricao,
                numero_planilha(c.valor),
                c.situacao,
            ]
        )

    return ("﻿" + saida.getvalue()).encode("utf-8")


# PDF


def gerar_pdf(resumo: ResumoExportado, comprimir: bool = True) -> bytes:
    """Documento para ler, imprimir ou mandar ao acompanhante (US38), no modelo único
    de PDF do Vero (`app/nucleo/pdf.py`)."""
    documento = DocumentoPdf(
        Message.TITULO.message, resumo.nome_do_mes.capitalize(), resumo.gerado_em
    )

    documento.secao(Message.SECAO_TOTAIS.message)
    documento.tabela(
        [[nome, moeda(valor)] for nome, valor in _totais(resumo)],
        [0.6, 0.4],
        cabecalho=False,
        destacar_ultima=True,
    )

    if resumo.categorias:
        documento.secao(Message.SECAO_CATEGORIAS.message)
        documento.tabela(
            [[Message.COLUNA_CATEGORIA.message, Message.COLUNA_VALOR.message]]
            + [[nome, moeda(valor)] for nome, valor in resumo.categorias],
            [0.6, 0.4],
        )

    documento.secao(Message.SECAO_REGISTROS.message)
    if resumo.registros:
        documento.tabela(
            [
                [
                    Message.COLUNA_DIA.message,
                    Message.COLUNA_TIPO.message,
                    Message.COLUNA_DESCRICAO.message,
                    Message.COLUNA_CATEGORIA.message,
                    Message.COLUNA_VALOR.message,
                ]
            ]
            + [
                [f"{r.dia:%d/%m}", _tipo(r), r.descricao, r.categoria, moeda(r.valor)]
                for r in resumo.registros
            ],
            [0.12, 0.14, 0.34, 0.2, 0.2],
        )
    else:
        documento.texto(Message.NADA_NO_MES.message)

    if resumo.contas_do_mes:
        documento.secao(Message.SECAO_CONTAS.message)
        documento.tabela(
            [
                [
                    Message.COLUNA_DIA_DE_PAGAR.message,
                    Message.COLUNA_DESCRICAO.message,
                    Message.COLUNA_VALOR.message,
                    Message.COLUNA_SITUACAO.message,
                ]
            ]
            + [
                [f"{c.dia_de_pagar:%d/%m}", c.descricao, moeda(c.valor), c.situacao]
                for c in resumo.contas_do_mes
            ],
            [0.2, 0.38, 0.22, 0.2],
        )

    return documento.gerar(comprimir)
