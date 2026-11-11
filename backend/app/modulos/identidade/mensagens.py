from enum import Enum


class Message(Enum):
    """Textos mostrados ao usuário, em linguagem simples (RNF02)."""

    TELEFONE_INVALIDO = "Digite o número do celular com DDD. Exemplo: 61 99999-8888."
    PIN_INVALIDO = "O PIN deve ter de 4 a 6 números."
    TELEFONE_JA_CADASTRADO = (
        "Este celular já está cadastrado. Tente entrar na sua conta."
    )
    EMAIL_JA_CADASTRADO = "Este e-mail já está cadastrado. Tente entrar na sua conta."
    PIN_ERRADO = "Celular ou PIN errados. Confira e tente de novamente."
    CONTA_BLOQUEADA = (
        "Muitas tentativas erradas. Espere {segundos} segundos e tente de novo."
    )
    SESSAO_INVALIDA = "Sua sessão terminou. Entre de novo na sua conta."

    def __init__(self, message: str) -> None:
        self.message = message
