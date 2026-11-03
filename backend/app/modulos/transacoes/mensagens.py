from enum import Enum


class Message(Enum):
    """Textos mostrados ao usuário, em linguagem simples (RNF02)."""

    VALOR_INVALIDO = "O valor precisa ser maior que zero."
    VALOR_MUITO_ALTO = "O valor é muito alto. Confira e tente novamente."

    def __init__(self, message: str):
        self.message = message
