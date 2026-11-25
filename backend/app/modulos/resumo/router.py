"""Rota de exportação do resumo das finanças (RF38)."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.modulos.identidade.modelos import Usuario
from app.modulos.identidade.seguranca import usuario_atual
from app.modulos.resumo import exportacao
from app.modulos.resumo.exportacao import Formato
from app.modulos.resumo.mensagens import Message
from app.nucleo.banco import obter_sessao

router = APIRouter(prefix="/api/v1/resumo", tags=["resumo"])

_TIPO_DO_ARQUIVO = {
    Formato.PDF: "application/pdf",
    Formato.CSV: "text/csv; charset=utf-8",
}


@router.get(
    "/exportar",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}, "text/csv": {}},
            "description": "Arquivo do resumo do mês, para baixar.",
        }
    },
)
def exportar(
    mes: str | None = None,
    formato: str = Formato.PDF,
    usuario: Usuario = Depends(usuario_atual),
    sessao: Session = Depends(obter_sessao),
) -> Response:
    """Resumo de um mês (`mes=AAAA-MM`; sem ele, o mês atual) em PDF ou CSV."""
    try:
        escolhido = Formato(formato.lower())
    except ValueError:
        raise _dado_errado(Message.FORMATO_INVALIDO) from None
    try:
        resumo = exportacao.montar(sessao, usuario.id, mes or exportacao.mes_atual())
    except exportacao.MesInvalido:
        raise _dado_errado(Message.MES_INVALIDO) from None

    conteudo = (
        exportacao.gerar_pdf(resumo)
        if escolhido == Formato.PDF
        else exportacao.gerar_csv(resumo)
    )
    nome = exportacao.nome_do_arquivo(resumo, escolhido)
    return Response(
        content=conteudo,
        media_type=_TIPO_DO_ARQUIVO[escolhido],
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


def _dado_errado(mensagem: Message) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, mensagem.message)
