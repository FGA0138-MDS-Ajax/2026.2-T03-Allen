from enum import Enum


class Message(Enum):
    """Textos mostrados ao usuário, em linguagem simples (RNF02)."""

    VALOR_INVALIDO = "O valor precisa ser maior que zero."
    VALOR_MUITO_ALTO = "O valor é muito alto. Confira e tente novamente."
    VALOR_EM_BRANCO = "Digite o valor. Ele não pode ficar em branco."
    DATA_EM_BRANCO = "Escolha a data. Ela não pode ficar em branco."
    CATEGORIA_INEXISTENTE = "Essa categoria não existe. Escolha outra."
    TRANSACAO_NAO_ENCONTRADA = (
        "Não encontramos esse lançamento. Atualize o histórico e tente de novo."
    )

    def __init__(self, message: str):
        self.message = message
