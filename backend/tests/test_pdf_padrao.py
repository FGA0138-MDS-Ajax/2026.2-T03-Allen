"""Testes do modelo único de PDF do Vero (app/nucleo/pdf.py)."""

import re
from datetime import date

from app.nucleo.pdf import DocumentoPdf


def _paginas(pdf: bytes) -> int:
    return len(re.findall(rb"/Type /Page\b", pdf))


def _textos(pdf: bytes) -> list[bytes]:
    """Trechos de texto desenhados na página. A reportlab grava acentos e o "·" em
    octal (ex.: \\343 é "ã") e quebra "<b>" em pedaços: "<", "b", ">"."""
    return [m[1:-4] for m in re.findall(rb"\((?:[^()\\]|\\.)*\) Tj", pdf)]


def test_gera_pdf_com_titulo_e_data() -> None:
    documento = DocumentoPdf("Resumo de teste", "Outubro de 2026", date(2026, 11, 24))
    documento.secao("Uma seção")
    documento.texto("Um texto.")

    pdf = documento.gerar(comprimir=False)

    assert pdf.startswith(b"%PDF")
    assert b"Resumo de teste" in pdf
    assert b"Outubro de 2026" in pdf
    assert b"Feito pelo Vero em 24/11/2026." in pdf


def test_rodape_com_numero_da_pagina_em_todas_as_paginas() -> None:
    documento = DocumentoPdf("Lista comprida")
    documento.tabela(
        [["Dia", "Valor"]] + [[f"{i:02d}/10", f"R$ {i},00"] for i in range(1, 90)],
        [0.5, 0.5],
    )

    pdf = documento.gerar(comprimir=False)

    total = _paginas(pdf)
    assert total >= 2
    for atual in range(1, total + 1):
        assert f"gina {atual} de {total}".encode() in pdf
    assert _textos(pdf).count(b"Vero \\267 Lista comprida") == total


def test_texto_com_simbolos_nao_quebra_o_documento() -> None:
    documento = DocumentoPdf("Símbolos")
    documento.texto("Arroz & feijão <b>promoção</b>")
    documento.tabela([["Descrição"], ["Pão & leite < R$ 10"]], [1.0])

    pdf = documento.gerar(comprimir=False)

    textos = _textos(pdf)
    # O "<b>" aparece escrito, em vez de virar negrito
    assert textos[textos.index(b"Arroz & feij\\343o <") :][:4] == [
        b"Arroz & feij\\343o <",
        b"b",
        b">",
        b"promo\\347\\343o",
    ]
    assert any(t.startswith(b"P\\343o & leite") for t in textos)


def test_titulo_vai_para_as_propriedades_do_arquivo() -> None:
    pdf = DocumentoPdf("Resumo das suas finanças").gerar(comprimir=False)

    assert b"/Author (Vero)" in pdf
    assert b"/Title (Resumo das suas finan" in pdf
