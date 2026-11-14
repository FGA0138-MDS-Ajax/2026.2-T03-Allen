from enum import Enum


class Message(Enum):
    """Textos mostrados ao usuário, em linguagem simples (RNF02)."""

    TEMPO_REAL_INDISPONIVEL = (
        "Não conseguimos atualizar a tela sozinhos agora. Recarregue a página."
    )

    def __init__(self, message: str):
        self.message = message
