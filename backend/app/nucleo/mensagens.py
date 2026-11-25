from enum import Enum


class Message(Enum):
    """Textos mostrados ao usuário usados por mais de um módulo (RNF02)."""

    # Documentos do Vero (PDF e planilhas)
    DOCUMENTO_GERADO_EM = "Feito pelo Vero em {data}."
    PDF_RODAPE = "Vero · {titulo}"
    PDF_PAGINA = "Página {atual} de {total}"

    def __init__(self, message: str) -> None:
        self.message = message
