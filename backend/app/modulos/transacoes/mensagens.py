from enum import Enum


class Message(Enum):
    """Textos mostrados ao usuário, em linguagem simples (RNF02)."""

    VALOR_INVALIDO = "O valor precisa ser maior que zero."
    VALOR_MUITO_ALTO = "O valor é muito alto. Confira e tente novamente."
    VALOR_E_DATA_OBRIGATORIOS = "O valor e a data não podem ficar em branco."
    CATEGORIA_INEXISTENTE = "Essa categoria não existe. Escolha outra."
    TRANSACAO_NAO_ENCONTRADA = (
        "Não encontramos esse lançamento. Atualize o histórico e tente de novo."
    )

    def __init__(self, message: str):
        self.message = message
