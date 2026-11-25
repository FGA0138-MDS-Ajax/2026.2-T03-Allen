"""Modelo único dos PDFs do Vero.

Todo PDF que o app gera usa esta classe, para ter a mesma aparência: letra grande e bom
contraste (RNF01), as mesmas margens, tabelas iguais e o mesmo rodapé em todas as páginas
("Vero · título" e "Página 1 de 2"). Quem gera o documento só diz o que vai nele:

    documento = DocumentoPdf("Resumo das suas finanças", "Outubro de 2026", hoje)
    documento.secao("Resumo do mês")
    documento.tabela([["Gastos", "R$ 10,00"]], [0.6, 0.4], cabecalho=False)
    conteudo = documento.gerar()
"""

import io
from datetime import date
from enum import Enum
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    CondPageBreak,
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.nucleo.mensagens import Message


class Padrao(Enum):
    """Medidas do modelo (tamanhos em pontos)."""

    TAMANHO_TITULO = 22
    TAMANHO_SUBTITULO = 16
    TAMANHO_SECAO = 16
    TAMANHO_TEXTO = 13
    TAMANHO_RODAPE = 10
    MARGEM_CM = 2
    ESPACO_ENTRE_SECOES_CM = 0.5
    # Com menos espaço que isto no fim da página, a seção começa na seguinte
    ESPACO_MINIMO_DA_SECAO_CM = 4


COR_LINHA = colors.HexColor("#999999")
COR_DESTAQUE = colors.HexColor("#E8E8E8")
COR_RODAPE = colors.HexColor("#444444")
MARGEM = Padrao.MARGEM_CM.value * cm

_BASE = getSampleStyleSheet()
_TITULO = ParagraphStyle(
    "vero-titulo",
    parent=_BASE["Title"],
    fontSize=Padrao.TAMANHO_TITULO.value,
    leading=Padrao.TAMANHO_TITULO.value + 6,
)
_SUBTITULO = ParagraphStyle(
    "vero-subtitulo",
    parent=_BASE["Heading2"],
    fontSize=Padrao.TAMANHO_SUBTITULO.value,
)
_SECAO = ParagraphStyle(
    "vero-secao",
    parent=_BASE["Heading2"],
    fontSize=Padrao.TAMANHO_SECAO.value,
)
_TEXTO = ParagraphStyle(
    "vero-texto",
    parent=_BASE["BodyText"],
    fontSize=Padrao.TAMANHO_TEXTO.value,
    leading=Padrao.TAMANHO_TEXTO.value + 4,
)
_NEGRITO = ParagraphStyle("vero-negrito", parent=_TEXTO, fontName="Helvetica-Bold")
_TABELA = [
    ("GRID", (0, 0), (-1, -1), 0.5, COR_LINHA),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]


def _paragrafo(texto: object, estilo: ParagraphStyle) -> Paragraph:
    """O texto vem de quem usa o app: '<' e '&' não podem virar marcação."""
    return Paragraph(escape(str(texto)), estilo)


def _canvas_com_rodape(rodape: str) -> type[canvas.Canvas]:
    """Canvas que guarda as páginas para saber o total antes de escrever o rodapé."""

    class CanvasComRodape(canvas.Canvas):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            self._paginas: list[dict] = []

        def showPage(self) -> None:  # noqa: N802 (nome da reportlab)
            self._paginas.append(dict(self.__dict__))
            self._startPage()

        def save(self) -> None:
            total = len(self._paginas)
            for pagina in self._paginas:
                self.__dict__.update(pagina)
                self._escrever_rodape(total)
                super().showPage()
            super().save()

        def _escrever_rodape(self, total: int) -> None:
            altura = MARGEM / 2
            self.setFont("Helvetica", Padrao.TAMANHO_RODAPE.value)
            self.setFillColor(COR_RODAPE)
            self.drawString(MARGEM, altura, rodape)
            self.drawRightString(
                A4[0] - MARGEM,
                altura,
                Message.PDF_PAGINA.message.format(atual=self._pageNumber, total=total),
            )

    return CanvasComRodape


class DocumentoPdf:
    """Documento A4 no padrão do Vero."""

    def __init__(
        self, titulo: str, subtitulo: str | None = None, gerado_em: date | None = None
    ) -> None:
        self.titulo = titulo
        self._partes: list[Flowable] = [_paragrafo(titulo, _TITULO)]
        if subtitulo:
            self._partes.append(_paragrafo(subtitulo, _SUBTITULO))
        if gerado_em:
            self.texto(
                Message.DOCUMENTO_GERADO_EM.message.format(data=f"{gerado_em:%d/%m/%Y}")
            )

    @property
    def largura_util(self) -> float:
        return A4[0] - 2 * MARGEM

    def secao(self, titulo: str) -> None:
        """O título nunca fica sozinho no fim da página: sem espaço para ele e algumas
        linhas, a seção começa na página seguinte. Com espaço, a tabela começa logo
        abaixo e continua na próxima página, sem deixar a página em branco."""
        self._partes += [
            Spacer(1, Padrao.ESPACO_ENTRE_SECOES_CM.value * cm),
            CondPageBreak(Padrao.ESPACO_MINIMO_DA_SECAO_CM.value * cm),
            _paragrafo(titulo, _SECAO),
        ]

    def texto(self, texto: str) -> None:
        self._partes.append(_paragrafo(texto, _TEXTO))

    def tabela(
        self,
        linhas: list[list[object]],
        proporcoes: list[float],
        cabecalho: bool = True,
        destacar_ultima: bool = False,
    ) -> None:
        """`proporcoes`: parte da largura de cada coluna (somam 1). A 1ª linha é o
        cabeçalho, repetido em cada página; a última pode sair em destaque (total)."""
        destaques = set()
        if cabecalho:
            destaques.add(0)
        if destacar_ultima:
            destaques.add(len(linhas) - 1)
        celulas = [
            [_paragrafo(c, _NEGRITO if i in destaques else _TEXTO) for c in linha]
            for i, linha in enumerate(linhas)
        ]
        tabela = Table(
            celulas,
            colWidths=[self.largura_util * p for p in proporcoes],
            repeatRows=1 if cabecalho else 0,
        )
        estilo = list(_TABELA)
        for i in destaques:
            estilo.append(("BACKGROUND", (0, i), (-1, i), COR_DESTAQUE))
        tabela.setStyle(TableStyle(estilo))
        self._partes.append(tabela)

    def gerar(self, comprimir: bool = True) -> bytes:
        saida = io.BytesIO()
        SimpleDocTemplate(
            saida,
            pagesize=A4,
            leftMargin=MARGEM,
            rightMargin=MARGEM,
            topMargin=MARGEM,
            bottomMargin=MARGEM,
            title=self.titulo,
            author="Vero",
            pageCompression=1 if comprimir else 0,
        ).build(
            self._partes,
            canvasmaker=_canvas_com_rodape(
                Message.PDF_RODAPE.message.format(titulo=self.titulo)
            ),
        )
        return saida.getvalue()
